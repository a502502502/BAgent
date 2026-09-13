#!/usr/bin/env python3
"""
services/football/squad_absence_checker.py
Squad & Absence Verification Engine (Regola #37, #38, #40).

Risolve definitivamente il problema delle allucinazioni anagrafiche:
1. Roster Gate: Verifica appartenenza alla rosa 2026/2027 (DB locale + API Transfers).
2. Absence Gate: Verifica infortuni, squalifiche e indisponibili (API /injuries).
3. Lineup Gate: Verifica titolarità ufficiale dal 1° minuto (API /fixtures/lineups).
"""

from __future__ import annotations
import sqlite3
import requests
import os
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "data" / "bagent.db"
if not DB_PATH.exists():
    DB_PATH = ROOT / "storage" / "database" / "bagent.db"

# Caricamento credenziali da .env
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#") and line.strip():
            k, _, v = line.partition("=")
            if k.strip() and v.strip():
                os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.getenv("API_FOOTBALL_KEY", "")
API_HOST = "v3.football.api-sports.io"
HEADERS = {
    "x-rapidapi-host": API_HOST,
    "x-rapidapi-key": API_KEY,
    "x-apisports-key": API_KEY,
}


def normalize(text: str) -> str:
    if not text:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    ).lower().replace("ı", "i").replace("ü", "u").replace("ö", "o").replace("é", "e").replace("è", "e")


def teams_match(team_a: str, team_b: str) -> bool:
    """Verifica se due nomi di squadra si riferiscono allo stesso club (es. Bayern Munich vs Bayern München vs Bayern Monaco)."""
    norm_a = normalize(team_a)
    norm_b = normalize(team_b)

    if norm_a == norm_b or norm_a in norm_b or norm_b in norm_a:
        return True

    # Token match (se condividono la parola chiave principale, es. "Bayern", "Fenerbahce", "Shakhtar", "Dortmund")
    stop_words = {"fc", "cf", "as", "ac", "de", "la", "the", "club", "calcio", "monaco", "munich", "munchen"}
    words_a = set(w for w in norm_a.replace("-", " ").replace("/", " ").split() if w not in stop_words and len(w) > 3)
    words_b = set(w for w in norm_b.replace("-", " ").replace("/", " ").split() if w not in stop_words and len(w) > 3)

    return len(words_a.intersection(words_b)) > 0


@dataclass
class PlayerAuditReport:
    player_name: str
    team_name: str
    in_squad: bool
    current_actual_team: str
    is_injured_or_suspended: bool
    injury_reason: str
    lineup_status: str  # "STARTER_CONFIRMED", "BENCH", "NOT_IN_SQUAD", "LINEUP_NOT_OUT"
    can_bet_player_prop: bool
    rejection_reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class SquadAbsenceChecker:
    """
    Motore di validazione anagrafica e medica dei giocatori.
    """

    def __init__(self, db_path: Path = DB_PATH, api_key: Optional[str] = None):
        self.db_path = db_path
        self.api_key = api_key or os.getenv("API_FOOTBALL_KEY", "")
        self.headers = {
            "x-rapidapi-host": API_HOST,
            "x-rapidapi-key": self.api_key,
            "x-apisports-key": self.api_key,
        }

    def _fetch_api(self, endpoint: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        url = f"https://{API_HOST}/{endpoint}"
        try:
            r = requests.get(url, headers=self.headers, params=params, timeout=12)
            if r.status_code == 200:
                data = r.json()
                return data.get("response", [])
        except Exception as e:
            print(f"[SquadAbsenceChecker] Errore chiamata {endpoint}: {e}")
        return []

    def check_player_in_db(self, player_name: str) -> List[Dict[str, Any]]:
        """Cerca il giocatore nel database SQLite locale."""
        if not self.db_path.exists():
            return []

        con = sqlite3.connect(self.db_path)
        con.create_function("NORM", 1, normalize)
        cur = con.cursor()
        norm_p = normalize(player_name)

        cur.execute("""
            SELECT player_id, name, number, position, age, team_id, team_name, league_name, last_updated
            FROM players
            WHERE NORM(name) LIKE ? OR NORM(name) LIKE ?
        """, (f"%{norm_p}%", f"{norm_p}%"))
        rows = cur.fetchall()
        con.close()

        results = []
        for r in rows:
            results.append({
                "player_id": r[0],
                "name": r[1],
                "number": r[2],
                "position": r[3],
                "age": r[4],
                "team_id": r[5],
                "team_name": r[6],
                "league_name": r[7],
                "last_updated": r[8]
            })
        return results

    def verify_player_roster(self, player_name: str, team_name: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Gate 1: Verifica se il giocatore appartiene al club indicato.
        Ritorna: (in_squad, actual_team, player_data)
        """
        # 1. Verifica DB Locale
        db_matches = self.check_player_in_db(player_name)
        for p in db_matches:
            if teams_match(team_name, p["team_name"]):
                return True, p["team_name"], p

        # Se trovato in DB ma in un'altra squadra -> Trasferito!
        if db_matches:
            actual = db_matches[0]["team_name"]
            return False, actual, db_matches[0]

        # 2. Controllo Live API Transfers
        profiles = self._fetch_api("players/profiles", {"search": player_name})
        if profiles:
            p_id = profiles[0].get("player", {}).get("id")
            p_name = profiles[0].get("player", {}).get("name", player_name)
            transfers_data = self._fetch_api("transfers", {"player": p_id})
            if transfers_data:
                tr_list = transfers_data[0].get("transfers", [])
                if tr_list:
                    latest_tr = tr_list[-1]
                    team_in = latest_tr.get("teams", {}).get("in", {}).get("name", "")
                    if teams_match(team_name, team_in):
                        return True, team_in, {"player_id": p_id, "name": p_name, "team_name": team_in}
                    else:
                        return False, team_in, {"player_id": p_id, "name": p_name, "team_name": team_in, "transfer": latest_tr}

        return False, "Sconosciuta / Non Trovata", {}

    def check_fixture_injuries(self, fixture_id: int) -> List[Dict[str, Any]]:
        """
        Recupera la lista ufficiale di infortunati, squalificati e indisponibili per una fixture.
        """
        return self._fetch_api("injuries", {"fixture": fixture_id})

    def check_player_injury(self, fixture_id: int, player_name: str) -> Tuple[bool, str]:
        """
        Gate 2: Verifica se il giocatore figura tra gli infortunati/squalificati per il match.
        Ritorna: (is_injured, reason)
        """
        injuries = self.check_fixture_injuries(fixture_id)
        norm_p = normalize(player_name)

        for inj in injuries:
            p = inj.get("player", {})
            p_name = p.get("name", "")
            inj_type = p.get("type", "Indisponibile")
            inj_reason = p.get("reason", "")

            if norm_p in normalize(p_name) or normalize(p_name) in norm_p:
                desc = f"{inj_type} ({inj_reason})" if inj_reason else inj_type
                return True, desc

        return False, ""

    def check_fixture_lineup(self, fixture_id: int, player_name: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Gate 3: Verifica le distinte ufficiali della partita.
        Ritorna: (status, details_str, raw_data)
        Status possibili: "STARTER_CONFIRMED", "BENCH", "NOT_IN_SQUAD", "LINEUP_NOT_OUT"
        """
        res = self._fetch_api("fixtures", {"id": fixture_id})
        if not res:
            return "LINEUP_NOT_OUT", "Dati fixture non disponibili", {}

        f = res[0]
        lineups = f.get("lineups", [])
        if not lineups:
            return "LINEUP_NOT_OUT", "Distinte ufficiali non ancora depositate (attese a 60' dall'inizio)", {}

        norm_p = normalize(player_name)

        for team_lineup in lineups:
            t_name = team_lineup.get("team", {}).get("name", "")
            starters = team_lineup.get("startXI", [])
            subs = team_lineup.get("substitutes", [])

            # Controllo Titolari
            for item in starters:
                p = item.get("player", {})
                if norm_p in normalize(p.get("name", "")) or normalize(p.get("name", "")) in norm_p:
                    return "STARTER_CONFIRMED", f"Titolare dal 1' per {t_name} (#{p.get('number')} {p.get('name')}, Ruolo: {p.get('pos')})", p

            # Controllo Panchina
            for item in subs:
                p = item.get("player", {})
                if norm_p in normalize(p.get("name", "")) or normalize(p.get("name", "")) in norm_p:
                    return "BENCH", f"In panchina per {t_name} (#{p.get('number')} {p.get('name')})", p

        return "NOT_IN_SQUAD", f"Non a referto per questo match", {}

    def full_player_audit(self, player_name: str, team_name: str, fixture_id: Optional[int] = None) -> PlayerAuditReport:
        """
        Esegue l'audit sequenziale completo:
        1. Roster Check (Regola #38)
        2. Injury & Absence Check
        3. Lineup & Starting XI Check (Regola #37)
        """
        # 1. Roster Check
        in_squad, actual_team, p_data = self.verify_player_roster(player_name, team_name)
        if not in_squad:
            return PlayerAuditReport(
                player_name=player_name,
                team_name=team_name,
                in_squad=False,
                current_actual_team=actual_team,
                is_injured_or_suspended=False,
                injury_reason="",
                lineup_status="N/A",
                can_bet_player_prop=False,
                rejection_reason=f"[BLOCCO REGOLA #38: TRASFERITO / SQUADRA ERRATA] {player_name} NON gioca per {team_name}! Squadra reale: '{actual_team}'.",
                details=p_data
            )

        # 2. Infortuni & Assenze (se fixture disponibile)
        is_injured = False
        inj_reason = ""
        if fixture_id:
            is_injured, inj_reason = self.check_player_injury(fixture_id, player_name)
            if is_injured:
                return PlayerAuditReport(
                    player_name=player_name,
                    team_name=team_name,
                    in_squad=True,
                    current_actual_team=actual_team,
                    is_injured_or_suspended=True,
                    injury_reason=inj_reason,
                    lineup_status="INJURED",
                    can_bet_player_prop=False,
                    rejection_reason=f"[BLOCCO INFORTUNIO / ASSENZA] {player_name} è indisponibile per questo match: {inj_reason}.",
                    details={"injury": inj_reason}
                )

        # 3. Controllo Formazione Ufficiale (Regola #37)
        lineup_status = "LINEUP_NOT_OUT"
        lineup_detail = ""
        if fixture_id:
            lineup_status, lineup_detail, lineup_p = self.check_fixture_lineup(fixture_id, player_name)
            if lineup_status == "LINEUP_NOT_OUT":
                return PlayerAuditReport(
                    player_name=player_name,
                    team_name=team_name,
                    in_squad=True,
                    current_actual_team=actual_team,
                    is_injured_or_suspended=False,
                    injury_reason="",
                    lineup_status="LINEUP_NOT_OUT",
                    can_bet_player_prop=False,
                    rejection_reason="[BLOCCO REGOLA #37] Distinte ufficiali non ancora disponibili. Vietato scommettere su mercati giocatore prima delle formazioni ufficiali!",
                    details={"note": lineup_detail}
                )
            elif lineup_status == "BENCH":
                return PlayerAuditReport(
                    player_name=player_name,
                    team_name=team_name,
                    in_squad=True,
                    current_actual_team=actual_team,
                    is_injured_or_suspended=False,
                    injury_reason="",
                    lineup_status="BENCH",
                    can_bet_player_prop=False,
                    rejection_reason=f"[BLOCCO REGOLA #37: PANCHINA] {player_name} parte dalla PANCHINA! ({lineup_detail}). Zero player props sui panchinari!",
                    details=lineup_p
                )
            elif lineup_status == "NOT_IN_SQUAD":
                return PlayerAuditReport(
                    player_name=player_name,
                    team_name=team_name,
                    in_squad=True,
                    current_actual_team=actual_team,
                    is_injured_or_suspended=False,
                    injury_reason="",
                    lineup_status="NOT_IN_SQUAD",
                    can_bet_player_prop=False,
                    rejection_reason=f"[BLOCCO REGOLA #37] {player_name} non figura nella distinta gara (né titolare né panchina).",
                    details={}
                )

        # Tutto verificato con successo!
        return PlayerAuditReport(
            player_name=player_name,
            team_name=team_name,
            in_squad=True,
            current_actual_team=actual_team,
            is_injured_or_suspended=False,
            injury_reason="",
            lineup_status=lineup_status,
            can_bet_player_prop=True,
            rejection_reason=None,
            details=p_data
        )

    def get_all_surnames_index(self) -> Dict[str, Tuple[str, str]]:
        """
        Indicizza tutti i cognomi dei giocatori registrati nel DB locale 2026/27.
        Ritorna: dict { normalized_surname: (full_name, team_name) }
        """
        if hasattr(self, "_surnames_cache") and self._surnames_cache:
            return self._surnames_cache

        import re
        cache = {}
        common_words = {
            'antonio', 'kevin', 'marco', 'david', 'lucas', 'andrea', 'daniel', 'mario',
            'alex', 'diego', 'carlos', 'felipe', 'martin', 'victor', 'pablo', 'sergio',
            'adrian', 'gabriel', 'alvaro', 'rodrigo', 'mateo', 'leonardo', 'nicolas',
            'julian', 'thomas', 'arthur', 'samuel', 'jorge', 'matias', 'alberto', 'federico',
            'mura', 'testa', 'forte', 'piano', 'campo', 'gioco', 'linea', 'punti', 'porto',
            'conte', 'conti', 'costa', 'silva', 'santos',
            'trafford', 'bernabeu', 'maradona', 'olimpico', 'anfield', 'etihad', 'emirates',
            'allianz', 'metropolitano', 'mestalla', 'balaidos', 'meazza', 'madrid', 'manchester',
            'london', 'paris', 'milan', 'roma', 'turin', 'naples', 'barcelona', 'bologna',
            'primo', 'secondo', 'tempo', 'tempi', 'partita', 'partite', 'squadra', 'squadre', 'minuto', 'minuti',
            'arena', 'stadium', 'stadio', 'ligue', 'league', 'serie', 'campionato', 'trasferta', 'europa', 'calcio', 'reale'
        }

        if self.db_path.exists():
            con = sqlite3.connect(self.db_path)
            cur = con.cursor()
            cur.execute("SELECT name, team_name FROM players")
            rows = cur.fetchall()
            con.close()

            for full_name, team_name in rows:
                parts = [p for p in re.split(r'[\s\.\-]+', full_name) if len(p) >= 5]
                if parts:
                    surname = parts[-1]
                    norm_s = normalize(surname)
                    if norm_s not in common_words and len(norm_s) >= 5:
                        cache[norm_s] = (full_name, team_name)

        self._surnames_cache = cache
        return cache

    def audit_text_entities(
        self,
        text: str,
        match_name: str,
        home_team: Optional[str] = None,
        away_team: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Regola #49: Zero Parametric Memory Gate.
        Scansiona il testo del Sesto Senso / motivazione per identificare allucinazioni
        di giocatori trasferiti, indisponibili o non appartenenti alle due squadre in campo.
        Ritorna: (passed, list_of_violations)
        """
        if not text or not text.strip():
            return True, []

        import re
        norm_text = " " + normalize(text) + " "

        # Risolvi squadre se non passate
        if not home_team or not away_team:
            for sep in [" vs ", " - ", " – ", " v "]:
                if sep in match_name:
                    parts = match_name.split(sep, 1)
                    home_team = parts[0].strip()
                    away_team = parts[1].strip()
                    break

        home_t = home_team or ""
        away_t = away_team or ""

        violations = []

        # 1. Controllo figure storiche notoriamente cedute o fuori rosa
        known_outdated = {
            'lukaku': ("Romelu Lukaku", "Non presente nella rosa del Napoli 2026/27"),
            'osimhen': ("Victor Osimhen", "Ceduto dal Napoli"),
            'zielinski': ("Piotr Zieliński", "Non milita più nel Napoli (trasferito all'Inter)"),
            'giroud': ("Olivier Giroud", "Non milita più in Serie A (MLS)"),
            'rabiot': ("Adrien Rabiot", "Non milita più nella Juventus"),
            'chiesa': ("Federico Chiesa", "Trasferito al Liverpool, non milita nella Juventus"),
        }

        for token, (name, note) in known_outdated.items():
            if re.search(rf"\b{re.escape(token)}\b", norm_text):
                # Se è citato a sproposito in un match correlato alla sua vecchia squadra
                if "napoli" in (home_t + away_t).lower() and token in ['lukaku', 'osimhen', 'zielinski']:
                    violations.append(f"Citazione anagrafica errata: '{name}' per il Napoli ({note}).")
                elif "juve" in (home_t + away_t).lower() and token in ['chiesa', 'rabiot']:
                    violations.append(f"Citazione anagrafica errata: '{name}' per la Juventus ({note}).")
                elif "milan" in (home_t + away_t).lower() and token in ['giroud']:
                    violations.append(f"Citazione anagrafica errata: '{name}' per il Milan ({note}).")

        # 2. Controllo allenatori non verificati o cambiati rispetto alle stagioni precedenti
        outdated_coaches = {
            'conte': ("Antonio Conte", "Non verificato o non più presente come guida tecnica del Napoli 2026/27"),
            'italiano': ("Vincenzo Italiano", "Non verificato o non più presente come guida tecnica del Bologna 2026/27"),
            'pioli': ("Stefano Pioli", "Non allena il Milan"),
            'allegri': ("Massimiliano Allegri", "Non allena la Juventus"),
            'sarri': ("Maurizio Sarri", "Non allena la Lazio"),
            'mourinho': ("José Mourinho", "Non allena la Roma"),
        }
        for token, (name, note) in outdated_coaches.items():
            if re.search(rf"\b{re.escape(token)}\b", norm_text):
                if "napoli" in (home_t + away_t).lower() and token == 'conte':
                    violations.append(f"Guida tecnica errata/non confermata: '{name}' per il Napoli ({note}).")
                elif "bologna" in (home_t + away_t).lower() and token == 'italiano':
                    violations.append(f"Guida tecnica errata/non confermata: '{name}' per il Bologna ({note}).")
                elif "milan" in (home_t + away_t).lower() and token == 'pioli':
                    violations.append(f"Guida tecnica errata: '{name}' per il Milan ({note}).")
                elif "juve" in (home_t + away_t).lower() and token == 'allegri':
                    violations.append(f"Guida tecnica errata: '{name}' per la Juventus ({note}).")

        # 2. Controllo incrociato su cognomi DB 2026/27
        surnames_index = self.get_all_surnames_index()
        tokens = re.findall(r'[a-zA-Z]{5,}', norm_text)
        norm_home = normalize(home_t)
        norm_away = normalize(away_t)
        for tok in set(tokens):
            if tok in norm_home or tok in norm_away:
                continue
            if tok in surnames_index:
                full_name, actual_team = surnames_index[tok]
                # Se il giocatore appartiene a un'altra squadra diversa da home e away
                if not teams_match(home_t, actual_team) and not teams_match(away_t, actual_team):
                    # Verifica che il token sia un match esatto nel testo
                    if re.search(rf"\b{re.escape(tok)}\b", norm_text):
                        violations.append(
                            f"Allucinazione anagrafica: '{full_name}' registrato nel '{actual_team}', NON appartiene a {home_t} né a {away_t}!"
                        )

        passed = len(violations) == 0
        return passed, violations

