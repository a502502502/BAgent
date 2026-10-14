#!/usr/bin/env python3
"""
services/football/reality_gate_guardian.py — Reality Gate Guardian 2026/27.

Custode attivo della realtà anagrafica e tecnica per BAgent (Regola #84, #85).
Intercetta e boccia tassativamente qualsiasi ticket, mercato, pronostico o testo
di analisi che contenga:
1. Allenatori obsoleti o allucinati (es. Mourinho al Fenerbahce o Roma, Pioli al Milan,
   Allegri alla Juve/Napoli, Sahin/Terzic al Dortmund, Guardiola al Man City, Klopp al Liverpool).
2. Giocatori attribuiti alla squadra errata (es. Sommer al Club Brugge, Wirtz al Leverkusen,
   Leao al Galatasaray, Hojlund al Napoli, Akanji all'Inter).
3. Roster non corrispondenti alla realtà della stagione calcistica 2026/27.

Opera su due livelli:
- DB SQLite persistente (official_team_managers_2026 e player_registry_2026).
- Audit semantico hard-gate integrato in strict_ticket_pipeline.py.
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DB_PATH = ROOT / "data" / "bagent.db"
STORAGE_DB_PATH = ROOT / "storage" / "database" / "bagent.db"


def normalize_text(text: str) -> str:
    """Normalizza testo rimuovendo accenti, cediglie e caratteri speciali."""
    if not text:
        return ""
    norm = unicodedata.normalize("NFD", text)
    cleaned = "".join(c for c in norm if unicodedata.category(c) != "Mn")
    cleaned = cleaned.lower()
    replacements = {
        "ı": "i", "ü": "u", "ö": "o", "é": "e", "è": "e", "ç": "c", "ş": "s",
        "ø": "o", "æ": "ae", "å": "a", "ł": "l", "đ": "d", "ß": "ss"
    }
    for k, v in replacements.items():
        cleaned = cleaned.replace(k, v)
    return cleaned


@dataclass
class ManagerProfile:
    team_name: str
    manager_name: str
    aliases: List[str] = field(default_factory=list)
    nationality: str = ""
    appointed_date: str = ""
    contract_until: str = ""
    former_managers_banned: List[str] = field(default_factory=list)
    formation: str = ""
    source: str = "TRANSFERMARKT_VERIFIED"
    last_verified: str = ""


@dataclass
class RealityAuditResult:
    is_valid: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    certified_entities: Dict[str, str] = field(default_factory=dict)


class RealityGateViolationError(Exception):
    """Sollevata quando un testo o ticket viola la realtà anagrafica 2026/27."""
    pass


class RealityGateGuardian:
    """
    Guardiano della realtà anagrafica e tecnica 2026/27.
    """

    def __init__(self, db_paths: Optional[List[Path]] = None):
        self.db_paths = db_paths or [DATA_DB_PATH, STORAGE_DB_PATH]
        self._ensure_tables()
        self._load_memory_caches()

    def _ensure_tables(self) -> None:
        """Crea le tabelle di riferimento se non esistono in entrambi i DB."""
        for path in self.db_paths:
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with sqlite3.connect(path) as conn:
                    cur = conn.cursor()
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS official_team_managers_2026 (
                            team_name TEXT PRIMARY KEY,
                            manager_name TEXT NOT NULL,
                            aliases TEXT,
                            nationality TEXT,
                            appointed_date TEXT,
                            contract_until TEXT,
                            former_managers_banned TEXT,
                            formation TEXT,
                            source TEXT DEFAULT 'TRANSFERMARKT_VERIFIED',
                            last_verified TEXT NOT NULL
                        )
                        """
                    )
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS player_registry_2026 (
                            canonical_name TEXT PRIMARY KEY,
                            display_name TEXT,
                            team_name TEXT NOT NULL,
                            former_teams TEXT,
                            role TEXT,
                            number INTEGER,
                            source TEXT DEFAULT 'TRANSFERMARKT_VERIFIED',
                            last_verified TEXT NOT NULL
                        )
                        """
                    )
                    conn.commit()
            except Exception as e:
                print(f"[RealityGateGuardian] Avviso creazione tabelle per {path}: {e}")

    def _load_memory_caches(self) -> None:
        """Carica in memoria la mappa degli allenatori e dei giocatori noti per rapidita d'audit."""
        self.managers: Dict[str, ManagerProfile] = {}
        self.banned_manager_map: Dict[str, List[Tuple[str, str]]] = {}  # banned_name -> [(team, actual_manager)]
        self.player_teams: Dict[str, str] = {}  # norm_player_name -> team_name
        self.former_team_map: Dict[str, List[str]] = {}  # norm_player_name -> [former_teams]

        # Carica da DB primario
        db_path = self.db_paths[0] if self.db_paths and self.db_paths[0].exists() else None
        if not db_path:
            return

        try:
            with sqlite3.connect(db_path) as conn:
                cur = conn.cursor()
                # 1. Managers
                rows = cur.execute(
                    "SELECT team_name, manager_name, aliases, nationality, appointed_date, contract_until, former_managers_banned, formation, source, last_verified FROM official_team_managers_2026"
                ).fetchall()
                for r in rows:
                    team, mgr, aliases_str, nat, app, con, banned_str, form, src, lver = r
                    aliases = [a.strip() for a in (aliases_str or "").split(",") if a.strip()]
                    banned = [b.strip() for b in (banned_str or "").split(",") if b.strip()]
                    prof = ManagerProfile(
                        team_name=team,
                        manager_name=mgr,
                        aliases=aliases,
                        nationality=nat or "",
                        appointed_date=app or "",
                        contract_until=con or "",
                        former_managers_banned=banned,
                        formation=form or "",
                        source=src or "TRANSFERMARKT_VERIFIED",
                        last_verified=lver or "",
                    )
                    self.managers[team.lower()] = prof

                    # Registra mappa ex allenatori banditi
                    for b in banned:
                        norm_b = normalize_text(b)
                        if norm_b not in self.banned_manager_map:
                            self.banned_manager_map[norm_b] = []
                        self.banned_manager_map[norm_b].append((team, mgr))

                # 2. Players
                p_rows = cur.execute(
                    "SELECT canonical_name, display_name, team_name, former_teams FROM player_registry_2026"
                ).fetchall()
                for r in p_rows:
                    canon, disp, team, formers_str = r
                    formers = [f.strip() for f in (formers_str or "").split(",") if f.strip()]
                    norm_c = normalize_text(canon)
                    norm_d = normalize_text(disp) if disp else ""
                    self.player_teams[norm_c] = team
                    if norm_d:
                        self.player_teams[norm_d] = team
                    if formers:
                        self.former_team_map[norm_c] = formers

        except Exception as e:
            print(f"[RealityGateGuardian] Avviso caricamento cache DB: {e}")

    def audit_text(
        self,
        text: str,
        home_team: Optional[str] = None,
        away_team: Optional[str] = None,
    ) -> RealityAuditResult:
        """
        Analizza un testo (motivazione, rassegna stampa, Sesto Senso, annotazioni)
        alla ricerca di allenatori obsoleti/allucinati e giocatori fuori squadra.
        """
        if not text:
            return RealityAuditResult(is_valid=True)

        norm_txt = normalize_text(text)
        violations: List[str] = []
        warnings: List[str] = []
        certified: Dict[str, str] = {}

        # 1. Controllo Allenatori Banditi
        for banned_norm, team_info_list in self.banned_manager_map.items():
            if re.search(rf"\b{re.escape(banned_norm)}\b", norm_txt):
                for team_name, actual_mgr in team_info_list:
                    norm_team = normalize_text(team_name)
                    # Verifica se il testo o il match contesto coinvolge questa squadra
                    is_context_match = False
                    if home_team and normalize_text(home_team) in norm_team or norm_team in normalize_text(home_team or ""):
                        is_context_match = True
                    elif away_team and normalize_text(away_team) in norm_team or norm_team in normalize_text(away_team or ""):
                        is_context_match = True
                    elif norm_team in norm_txt:
                        is_context_match = True

                    if is_context_match:
                        violations.append(
                            f"ALLUCINAZIONE ALLENATORE: Il testo menziona '{banned_norm.title()}' associato a '{team_name}'. "
                            f"L'allenatore ufficiale per la stagione 2026/27 e '{actual_mgr}'. "
                            f"'{banned_norm.title()}' non siede piu sulla panchina di questa squadra!"
                        )

        # 2. Controllo Coerenza Allenatore Attivo (se menzionato, certifica)
        for team_key, prof in self.managers.items():
            norm_mgr = normalize_text(prof.manager_name)
            mgr_surname = normalize_text(prof.manager_name.split()[-1])
            if re.search(rf"\b{re.escape(mgr_surname)}\b", norm_txt) or re.search(rf"\b{re.escape(norm_mgr)}\b", norm_txt):
                certified[prof.team_name] = f"Allenatore certificato: {prof.manager_name}"

        # 3. Controllo Ex Squadre Giocatori Trasferiti (Anti-Memory Bias)
        for norm_player, formers in self.former_team_map.items():
            player_surname = norm_player.split(",")[0].strip() if "," in norm_player else norm_player.split()[-1].strip()
            if len(player_surname) >= 4 and re.search(rf"\b{re.escape(player_surname)}\b", norm_txt):
                actual_team = self.player_teams.get(norm_player, "")
                for former in formers:
                    norm_former = normalize_text(former)
                    pattern = rf"({re.escape(player_surname)}).{{0,30}}({re.escape(norm_former)})|({re.escape(norm_former)}).{{0,30}}({re.escape(player_surname)})"
                    if re.search(pattern, norm_txt):
                        violations.append(
                            f"ALLUCINAZIONE TRASFERIMENTO: '{norm_player.title()}' e associato a '{former}', "
                            f"ma e un ex giocatore! Nella stagione 2026/27 milita ufficialmente in '{actual_team}'."
                        )

        # 4. Controllo Associazione Giocatore-Squadra Esplicita (es. 'Sommer (Club Brugge)' o 'Leao (Galatasaray)')
        for norm_player, actual_team in self.player_teams.items():
            player_surname = norm_player.split(",")[0].strip() if "," in norm_player else norm_player.split()[-1].strip()
            if len(player_surname) < 4:
                continue
            # Fast substring filter: se il cognome non compare affatto nel testo, salta all'istante
            if player_surname not in norm_txt:
                continue
            # Pattern 1: Cognome (Squadra) o Nome Cognome (Squadra)
            matches = re.finditer(rf"\b{re.escape(player_surname)}\b[^\(]{{0,15}}\(([^)]+)\)", norm_txt)
            for m in matches:
                parenthesis_team = m.group(1).strip()
                norm_pt = normalize_text(parenthesis_team)
                norm_at = normalize_text(actual_team)
                if norm_pt not in norm_at and norm_at not in norm_pt:
                    # Verifica che non sia una lega o un ruolo (es. 'rigorista', 'capitano')
                    if any(t_known in norm_pt for t_known in self.managers.keys()):
                        violations.append(
                            f"ALLUCINAZIONE ATTRIBUZIONE: '{norm_player.title()}' e indicato come giocatore di '({parenthesis_team})', "
                            f"ma nel 2026/27 milita ufficialmente in '{actual_team}'!"
                        )

            # Pattern 2: Cognome del/della/dell'/di/nel/nell'/al/all'/in Squadra
            matches_prep = re.finditer(rf"\b{re.escape(player_surname)}\b\s+(?:del|della|dello|dell'|dei|degli|delle|di|nel|nella|nello|nell'|nei|negli|nelle|in|al|alla|allo|all'|ai|agli|alle)\s*([A-Za-zÀ-ÿ'\s-]{{3,25}})", norm_txt)
            for mp in matches_prep:
                target_cand = mp.group(1).strip()
                norm_tc = normalize_text(target_cand)
                norm_at = normalize_text(actual_team)
                for t_known in self.managers.keys():
                    if t_known in norm_tc and t_known not in norm_at:
                        violations.append(
                            f"ALLUCINAZIONE ATTRIBUZIONE: '{norm_player.title()}' e associato a '{t_known.title()}', "
                            f"ma nel 2026/27 milita ufficialmente in '{actual_team}'!"
                        )
                        break

        return RealityAuditResult(
            is_valid=len(violations) == 0,
            violations=violations,
            warnings=warnings,
            certified_entities=certified,
        )

    def audit_player_attribution(self, player_name: str, team_name: str) -> Tuple[bool, str]:
        """
        Verifica che il giocatore appartenga effettivamente alla squadra specificata nel 2026/27.
        """
        norm_p = normalize_text(player_name)
        norm_t = normalize_text(team_name)

        # Cerca nel registro memoria
        registered_team = None
        for k, v in self.player_teams.items():
            if norm_p in k or k in norm_p:
                registered_team = v
                break

        if registered_team:
            norm_reg = normalize_text(registered_team)
            if norm_t in norm_reg or norm_reg in norm_t:
                return True, f"OK: {player_name} milita regolarmente in {registered_team} (2026/27)."
            else:
                return False, (
                    f"BLOCCO ATTRIBUZIONE: {player_name} NON gioca in '{team_name}'! "
                    f"Dalla registrazione ufficiale 2026/27 milita in '{registered_team}'."
                )

        # Se non in cache memoria, interroga DB
        for path in self.db_paths:
            if not path.exists():
                continue
            try:
                with sqlite3.connect(path) as conn:
                    cur = conn.cursor()
                    row = cur.execute(
                        """
                        SELECT team_name FROM player_registry_2026
                        WHERE canonical_name LIKE ? OR display_name LIKE ?
                        LIMIT 1
                        """,
                        (f"%{player_name}%", f"%{player_name}%"),
                    ).fetchone()
                    if row:
                        db_team = row[0]
                        norm_db = normalize_text(db_team)
                        if norm_t in norm_db or norm_db in norm_t:
                            return True, f"OK: {player_name} milita regolarmente in {db_team} (2026/27)."
                        else:
                            return False, (
                                f"BLOCCO ATTRIBUZIONE: {player_name} NON gioca in '{team_name}'! "
                                f"Registro 2026/27 attesta l'appartenenza a '{db_team}'."
                            )
            except Exception:
                pass

        return True, f"AVVISO: {player_name} non censito espressamente in player_registry_2026 (procedere con verifica esterna)."

    def audit_candidate(self, candidate: Any) -> Tuple[bool, Optional[str]]:
        """
        Esegue l'audit completo pre-schedina su un MarketCandidate.
        Controlla:
        - Nome match e mercati (se contengono player props)
        - sixth_sense_analysis (audit semantico allenatori e trasferimenti)
        - Player attribution esplicita
        """
        # 1. Audit del testo di Sesto Senso
        analysis_txt = getattr(candidate, "sixth_sense_analysis", "") or ""
        match_name = getattr(candidate, "match_name", "") or ""
        home_team = match_name.split(" vs ")[0].strip() if " vs " in match_name else None
        away_team = match_name.split(" vs ")[1].strip() if " vs " in match_name else None

        audit_res = self.audit_text(analysis_txt, home_team=home_team, away_team=away_team)
        if not audit_res.is_valid:
            rejection = " | ".join(audit_res.violations)
            return False, f"[BLOCCATO - REALITY GATE GUARDIAN (Regola #84/#85)] {rejection}"

        # 2. Audit del nome mercato (nel caso contenga player props, es. 'Sommer (Club Brugge)')
        market_name = getattr(candidate, "market_name", "") or ""
        m_audit = self.audit_text(market_name, home_team=home_team, away_team=away_team)
        if not m_audit.is_valid:
            rejection = " | ".join(m_audit.violations)
            return False, f"[BLOCCATO - REALITY GATE GUARDIAN: MERCATO NON VALIDO] {rejection}"

        # 3. Audit dell'attribuzione giocatore se presente
        p_name = getattr(candidate, "player_name", None)
        t_name = getattr(candidate, "team_name", None)
        if p_name and t_name:
            p_ok, p_msg = self.audit_player_attribution(p_name, t_name)
            if not p_ok:
                return False, f"[BLOCCATO - REALITY GATE GUARDIAN] {p_msg}"

        return True, None

    def register_manager(
        self,
        team_name: str,
        manager_name: str,
        aliases: Optional[List[str]] = None,
        nationality: str = "",
        appointed_date: str = "",
        contract_until: str = "",
        former_managers_banned: Optional[List[str]] = None,
        formation: str = "",
        source: str = "TRANSFERMARKT_VERIFIED",
    ) -> None:
        """Registra o aggiorna un allenatore ufficiale in entrambi i database."""
        now_str = datetime.now(timezone.utc).isoformat()
        aliases_str = ", ".join(aliases) if aliases else ""
        banned_str = ", ".join(former_managers_banned) if former_managers_banned else ""

        for path in self.db_paths:
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with sqlite3.connect(path) as conn:
                    cur = conn.cursor()
                    cur.execute(
                        """
                        INSERT INTO official_team_managers_2026 (
                            team_name, manager_name, aliases, nationality, appointed_date,
                            contract_until, former_managers_banned, formation, source, last_verified
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(team_name) DO UPDATE SET
                            manager_name=excluded.manager_name,
                            aliases=excluded.aliases,
                            nationality=excluded.nationality,
                            appointed_date=excluded.appointed_date,
                            contract_until=excluded.contract_until,
                            former_managers_banned=excluded.former_managers_banned,
                            formation=excluded.formation,
                            source=excluded.source,
                            last_verified=excluded.last_verified
                        """,
                        (
                            team_name,
                            manager_name,
                            aliases_str,
                            nationality,
                            appointed_date,
                            contract_until,
                            banned_str,
                            formation,
                            source,
                            now_str,
                        ),
                    )
                    conn.commit()
            except Exception as e:
                print(f"[RealityGateGuardian] Errore salvataggio manager su {path}: {e}")

        # Aggiorna cache memoria
        prof = ManagerProfile(
            team_name=team_name,
            manager_name=manager_name,
            aliases=aliases or [],
            nationality=nationality,
            appointed_date=appointed_date,
            contract_until=contract_until,
            former_managers_banned=former_managers_banned or [],
            formation=formation,
            source=source,
            last_verified=now_str,
        )
        self.managers[team_name.lower()] = prof
        if former_managers_banned:
            for b in former_managers_banned:
                norm_b = normalize_text(b)
                if norm_b not in self.banned_manager_map:
                    self.banned_manager_map[norm_b] = []
                self.banned_manager_map[norm_b].append((team_name, manager_name))

    def register_player(
        self,
        canonical_name: str,
        display_name: str,
        team_name: str,
        former_teams: Optional[List[str]] = None,
        role: str = "",
        number: Optional[int] = None,
        source: str = "TRANSFERMARKT_VERIFIED",
    ) -> None:
        """Registra o aggiorna un giocatore nel registro 2026/27 in entrambi i database."""
        now_str = datetime.now(timezone.utc).isoformat()
        formers_str = ", ".join(former_teams) if former_teams else ""

        for path in self.db_paths:
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with sqlite3.connect(path) as conn:
                    cur = conn.cursor()
                    cur.execute(
                        """
                        INSERT INTO player_registry_2026 (
                            canonical_name, display_name, team_name, former_teams,
                            role, number, source, last_verified
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(canonical_name) DO UPDATE SET
                            display_name=excluded.display_name,
                            team_name=excluded.team_name,
                            former_teams=excluded.former_teams,
                            role=excluded.role,
                            number=excluded.number,
                            source=excluded.source,
                            last_verified=excluded.last_verified
                        """,
                        (
                            canonical_name,
                            display_name,
                            team_name,
                            formers_str,
                            role,
                            number,
                            source,
                            now_str,
                        ),
                    )
                    conn.commit()
            except Exception as e:
                print(f"[RealityGateGuardian] Errore salvataggio player su {path}: {e}")

        # Aggiorna cache memoria
        norm_c = normalize_text(canonical_name)
        self.player_teams[norm_c] = team_name
        if display_name:
            self.player_teams[normalize_text(display_name)] = team_name
        if former_teams:
            self.former_team_map[norm_c] = former_teams
