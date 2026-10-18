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

from services.football.reality_gate_guardian import RealityGateGuardian

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
        self.guardian = RealityGateGuardian(db_paths=[self.db_path])
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
        """Cerca il giocatore nel database SQLite locale (prima player_registry_2026, poi players)."""
        if not self.db_path.exists():
            return []

        norm_p = normalize(player_name)
        results = []

        try:
            with sqlite3.connect(self.db_path) as con:
                con.create_function("NORM", 1, normalize)
                cur = con.cursor()

                # 1. Priorita assoluta al Registro Ufficiale 2026/27
                try:
                    cur.execute("""
                        SELECT canonical_name, display_name, team_name, role, number, source, last_verified
                        FROM player_registry_2026
                        WHERE NORM(canonical_name) LIKE ? OR NORM(display_name) LIKE ?
                    """, (f"%{norm_p}%", f"%{norm_p}%"))
                    for r in cur.fetchall():
                        results.append({
                            "player_id": None,
                            "name": r[0],
                            "display_name": r[1],
                            "team_name": r[2],
                            "position": r[3] or "N/D",
                            "number": r[4],
                            "source": r[5],
                            "season": "2026/27",
                            "last_updated": r[6]
                        })
                    if results:
                        return results
                except sqlite3.OperationalError:
                    pass

                # 2. Fallback alla tabella players storica con le colonne reali
                cur.execute("""
                    SELECT id, full_name, current_club, position, age, league, season
                    FROM players
                    WHERE NORM(full_name) LIKE ?
                """, (f"%{norm_p}%",))
                for r in cur.fetchall():
                    results.append({
                        "player_id": r[0],
                        "name": r[1],
                        "team_name": r[2],
                        "position": r[3] or "N/D",
                        "age": r[4],
                        "league_name": r[5],
                        "season": r[6],
                        "source": "DB_PLAYERS_HISTORICAL"
                    })
                return results
        except Exception as e:
            print(f"[SquadAbsenceChecker] Avviso ricerca DB per {player_name}: {e}")
            return []

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

    def check_flashscore_lineup(self, flashscore_match_id: str, player_name: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Regola #88: Verifica le formazioni ufficiali su Flashscore (df_li_1_<match_id>).
        Ritorna: (status, details_str, raw_data)
        Status: "STARTER_CONFIRMED", "BENCH", "NOT_IN_SQUAD", "LINEUP_NOT_OUT"
        """
        if not flashscore_match_id:
            return "LINEUP_NOT_OUT", "ID match Flashscore non specificato", {}
        url = f"https://2.flashscore.ninja/2/x/feed/df_li_1_{flashscore_match_id}"
        try:
            r = requests.get(url, headers={"X-Fsign": "SW9D1eZo", "User-Agent": "Mozilla/5.0"}, timeout=10)
            if r.status_code != 200 or not r.text or "Starting Lineups" not in r.text:
                return "LINEUP_NOT_OUT", "Formazioni ufficiali (Starting Lineups) non ancora pubblicate su Flashscore", {}
            text = r.text
            # Estrai i blocchi per sezione (Starting Lineups vs Substitutes)
            import re
            sections = text.split("~LB÷")
            norm_target = normalize(player_name)
            # Gestisci formato "Cognome, Nome" -> tokens
            target_tokens = [t for t in re.split(r"[\s,\.\-]+", norm_target) if len(t) >= 3]
            surname_tok = target_tokens[0] if target_tokens else norm_target

            starters_list: List[str] = []
            subs_list: List[str] = []

            for sec in sections:
                sec_header = sec.split("¬")[0].strip() if "¬" in sec else ""
                players_in_sec = re.findall(r"LI÷([^¬]+)", sec)
                if "Starting Lineups" in sec_header or "Formazioni" in sec_header:
                    starters_list.extend(players_in_sec)
                elif "Substitutes" in sec_header or "Panchina" in sec_header or "Sostituti" in sec_header:
                    subs_list.extend(players_in_sec)

            if not starters_list:
                return "LINEUP_NOT_OUT", "Lista titolari (Starting Lineups) vuota su Flashscore", {}

            for p in starters_list:
                np = normalize(p)
                if surname_tok in np or np in norm_target:
                    return "STARTER_CONFIRMED", f"Titolare Ufficiale dal 1' certificato su Flashscore ({p})", {"player": p, "source": "flashscore_df_li_1"}

            for p in subs_list:
                np = normalize(p)
                if surname_tok in np or np in norm_target:
                    return "BENCH", f"PANCHINARO nella distinta ufficiale Flashscore ({p})", {"player": p, "source": "flashscore_df_li_1"}

            return "NOT_IN_SQUAD", f"Assente dalla distinta ufficiale Flashscore (né nei 22 titolari né in panchina)", {"starters_count": len(starters_list)}
        except Exception as e:
            return "LINEUP_NOT_OUT", f"Errore verifica Flashscore df_li_1: {e}", {}

    def full_player_audit(
        self,
        player_name: str,
        team_name: str,
        fixture_id: Optional[int] = None,
        flashscore_match_id: Optional[str] = None,
        official_starter_verified: bool = False,
    ) -> PlayerAuditReport:
        """
        Esegue l'audit sequenziale completo (Regole #37, #38, #84, #88):
        1. Roster Check (Regola #38 / #84)
        2. Injury & Absence Check
        3. Lineup & Starting XI Check (Regola #37 & Regola #88 — Obbligo Formazione Ufficiale Titolare dal 1')
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
                rejection_reason=f"[BLOCCO REGOLA #38/#84: TRASFERITO / SQUADRA ERRATA] {player_name} NON gioca per {team_name}! Squadra reale: '{actual_team}'.",
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

        # 3. Controllo Formazione Ufficiale (Regola #37 & Regola #88)
        lineup_status = "LINEUP_NOT_OUT"
        lineup_detail = "Distinta ufficiale non verificata"
        lineup_p: Dict[str, Any] = {}

        if flashscore_match_id:
            lineup_status, lineup_detail, lineup_p = self.check_flashscore_lineup(flashscore_match_id, player_name)
        elif fixture_id:
            lineup_status, lineup_detail, lineup_p = self.check_fixture_lineup(fixture_id, player_name)
        elif official_starter_verified:
            lineup_status = "STARTER_CONFIRMED"
            lineup_detail = "Titolare ufficiale dal 1' verificato su distinta ufficiale"

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
                rejection_reason=(
                    f"[BLOCCO REGOLA #88: FORMAZIONE UFFICIALE NON ANCORA PUBBLICATA] Impossibile scommettere su '{player_name}' ({team_name}). "
                    f"È tassativamente vietato fare scommesse su singoli giocatori se non sono ufficialmente nella formazione titolare ufficiale "
                    f"già pubblicata (Starting Lineups df_li_1_). Dettaglio: {lineup_detail}."
                ),
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
                rejection_reason=(
                    f"[BLOCCO REGOLA #88: GIOCATORE IN PANCHINA] '{player_name}' ({team_name}) parte dalla PANCHINA nella formazione ufficiale! "
                    f"({lineup_detail}). Divieto assoluto di scommettere su giocatori non titolari dal 1'!"
                ),
                details=lineup_p
            )
        elif lineup_status != "STARTER_CONFIRMED":
            return PlayerAuditReport(
                player_name=player_name,
                team_name=team_name,
                in_squad=True,
                current_actual_team=actual_team,
                is_injured_or_suspended=False,
                injury_reason="",
                lineup_status=lineup_status,
                can_bet_player_prop=False,
                rejection_reason=(
                    f"[BLOCCO REGOLA #88: NON TITOLARE NELLA FORMAZIONE UFFICIALE] '{player_name}' non figura nell'11 titolare ufficiale ({lineup_detail})."
                ),
                details=lineup_p
            )

        # Tutto verificato con successo: in rosa, sano e TITOLARE UFFICIALE DAL 1'!
        return PlayerAuditReport(
            player_name=player_name,
            team_name=team_name,
            in_squad=True,
            current_actual_team=actual_team,
            is_injured_or_suspended=False,
            injury_reason="",
            lineup_status="STARTER_CONFIRMED",
            can_bet_player_prop=True,
            rejection_reason=None,
            details={**p_data, **lineup_p, "lineup_detail": lineup_detail}
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
            try:
                with sqlite3.connect(self.db_path) as con:
                    cur = con.cursor()
                    cur.execute("SELECT name, team_name FROM players")
                    rows = cur.fetchall()

                    for full_name, team_name in rows:
                        parts = [p for p in re.split(r'[\s\.\-]+', full_name) if len(p) >= 5]
                        if parts:
                            surname = parts[-1]
                            norm_s = normalize(surname)
                            if norm_s not in common_words and len(norm_s) >= 5:
                                cache[norm_s] = (full_name, team_name)
            except sqlite3.OperationalError:
                pass

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
        Regola #49, #84, #85: Reality Gate Guardian Audit.
        Scansiona il testo del Sesto Senso / motivazione per identificare allucinazioni
        di allenatori obsoleti o giocatori non appartenenti alla rosa 2026/27.
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

        # 1. Audit autoritativo via RealityGateGuardian
        guardian_res = self.guardian.audit_text(text, home_team=home_t, away_team=away_t)
        violations = list(guardian_res.violations)

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

