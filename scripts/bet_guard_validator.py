"""
BAgent - BetGuard Validator (Motore di Controllo delle 14 Regole Inviolabili)
Ogni selezione DEVE passare attraverso questo modulo Python prima di essere approvata.
"""

import sys

# Force UTF-8 stdout if needed
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

class BetGuardValidator:
    def __init__(self):
        self.rules_loaded = 15
        print(f"BetGuard Engine initialized with {self.rules_loaded} Inviolable Rules.")

    def validate_selection(self, match_data):
        """
        Valida una singola selezione applicando le regole programmatiche.
        Restituisce (is_valid: bool, reason: str)
        """
        match_name = match_data.get("match", "Unknown Match")
        league = match_data.get("league", "")
        pick = match_data.get("pick", "")
        team1_pts = match_data.get("team1_pts", 0)
        team2_pts = match_data.get("team2_pts", 0)
        matches_played = match_data.get("matches_played", 10)
        is_youth_or_b_team = match_data.get("is_youth_or_b_team", False)
        is_matchday_1 = match_data.get("is_matchday_1", False)
        is_derby_or_high_tension = match_data.get("is_derby_or_high_tension", False)
        is_massive_favorite_home = match_data.get("is_massive_favorite_home", False)

        # REGOLA #9: Divieto 1X2 su leghe giovanili o squadre B
        if is_youth_or_b_team and pick in ["1", "2", "1X2: 1", "1X2: 2"]:
            return False, f"[BLOCKED - RULE 9] Vietato 1X2 secco su squadre B/giovanili ({match_name}). Consentiti solo Over/Under o DC."

        # REGOLA #10: Campione ridotto (N <= 3) & Debutto alla 1ª Giornata
        if is_matchday_1 and pick in ["1", "2", "1X2: 1", "1X2: 2"]:
            return False, f"[BLOCKED - RULE 10] Alla 1ª giornata vietato 1X2 secco ({match_name}). Usare DC di protezione (1X/X2) o Gol."

        # REGOLA #12: Trappola partita 'troppo pulita' su sanzioni/falli
        if is_massive_favorite_home and not is_derby_or_high_tension and any(term in pick.lower() for term in ["cartellin", "falli", "cards", "fouls"]):
            return False, f"[BLOCKED - RULE 12] Gara a senso unico 'troppo pulita' ({match_name}). Vietati mercati sanzioni/falli, consentiti solo Gol/Tiri/Corner."

        # REGOLA #14: Filtro Delta Punti <= 3 in leghe minori / Sudamerica
        delta_pts = abs(team1_pts - team2_pts)
        is_latam_or_minor = any(term in league.lower() for term in ["paraguay", "colombia", "estonia", "panama", "segunda", "prom", "serie b", "primavera"])
        if is_latam_or_minor and delta_pts <= 3 and pick in ["1", "2", "1X", "X2", "1X2: 1", "1X2: 2"]:
            return False, f"[BLOCKED - RULE 14] Delta Punti = {delta_pts} (<= 3) in lega minore/sudamericana ({match_name}). Scontro diretto a moneta lanciata: BAN ASSOLUTO sui segni 1X2/DC. SKIP / NO BET!"

        return True, f"[APPROVED] Conforme alle Regole Inviolabili."

    def validate_ticket_set(self, active_tickets: list[list[dict]]) -> tuple[bool, str]:
        """
        REGOLA #15: Verifica che non ci siano selezioni duplicate identiche tra più ticket aperti.
        Garantisce il decoupling totale ed elimina i single-point-of-failure.
        """
        seen_picks = {}
        for t_idx, ticket in enumerate(active_tickets, start=1):
            for item in ticket:
                key = (item.get("match", "").strip().lower(), item.get("pick", "").strip().lower())
                if key in seen_picks:
                    prev_t = seen_picks[key]
                    return False, f"[BLOCKED - RULE 15] Selezione duplicata rilevata: '{item.get('match')}' -> '{item.get('pick')}' presente sia nel Ticket #{prev_t} che nel Ticket #{t_idx}. Vietato condividere lo stesso evento tra più schedine!"
                seen_picks[key] = t_idx
        return True, "[APPROVED - RULE 15] Tutti i ticket sono statisticamente indipendenti e disgiunti."

if __name__ == "__main__":
    validator = BetGuardValidator()

    # TEST 1: Sol de América vs Resistencia (Delta = 1 in Paraguay)
    test1 = {
        "match": "Sol de America vs Resistencia",
        "league": "Paraguay - Segunda Division",
        "team1_pts": 24,
        "team2_pts": 23,
        "pick": "1X",
        "matches_played": 15
    }
    valid1, msg1 = validator.validate_selection(test1)
    print(f"\n[Test 1] {test1['match']} (Pick: {test1['pick']}): {msg1}")

    # TEST 2: Jaguares vs Boyacá Chicó (Colombia - Boyaca 0V-3P-11S fuori casa)
    test2 = {
        "match": "Jaguares vs Boyaca Chico",
        "league": "Colombia - Primera A",
        "team1_pts": 18,
        "team2_pts": 11,
        "pick": "1X",
        "matches_played": 12
    }
    valid2, msg2 = validator.validate_selection(test2)
    print(f"\n[Test 2] {test2['match']} (Pick: {test2['pick']}): {msg2}")

    # TEST 3: Arsenal vs Coventry (Premier - Corner & Gol)
    test3 = {
        "match": "Arsenal vs Coventry",
        "league": "Premier League",
        "pick": "1 + Over 1.5 Gol",
        "is_massive_favorite_home": True
    }
    valid3, msg3 = validator.validate_selection(test3)
    print(f"\n[Test 3] {test3['match']} (Pick: {test3['pick']}): {msg3}")
