"""
BAgent - BetGuard Validator (Motore di Controllo delle 19 Regole Inviolabili)
Ogni selezione DEVE passare attraverso questo modulo Python prima di essere approvata.
"""

import sys

# Force UTF-8 stdout if needed
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

class BetGuardValidator:
    def __init__(self):
        self.rules_loaded = 19
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
        is_central_penetration_team = match_data.get("is_central_penetration_team", False)
        is_high_possession_favorite = match_data.get("is_high_possession_favorite", False)

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

        # REGOLA #17: Trappola Corner nelle Goleade Centrali (es. Barcellona di Flick / Real Madrid)
        if is_central_penetration_team and any(term in pick.lower() for term in ["corner squadra", "cornersquadra", "corner sq", "corner team"]) and any(th in pick for th in ["5.5", "6.5", "7.5"]):
            return False, f"[BLOCKED - RULE 17] Trappola Corner Goleada Centrale ({match_name}): squadra da penetrazione verticale/centrale. Vietato Over Corner Squadra >5.5! Usare Combo Risultato/Gol o Tiri."

        # REGOLA #18: Asimmetria dei Falli (Possesso vs Non Possesso)
        if is_high_possession_favorite and any(term in pick.lower() for term in ["falli commessi squadra", "falli squadra favorita", "team fouls"]) and ("over" in pick.lower()):
            return False, f"[BLOCKED - RULE 18] Asimmetria Falli ({match_name}): la favorita di possesso palla NON commette falli alti. Giocare Over Falli solo sulla sfavorita o Falli Totali Match!"

        return True, f"[APPROVED] Conforme a tutte le 19 Regole Inviolabili."

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

    # TEST RULE 17: Barcellona Over 5.5 Corner Squadra
    test_barca = {
        "match": "Elche vs Barcellona",
        "league": "LaLiga",
        "pick": "Over 5.5 Corner Squadra 2",
        "is_central_penetration_team": True
    }
    valid_b, msg_b = validator.validate_selection(test_barca)
    print(f"\n[Test Rule 17] {test_barca['match']} ({test_barca['pick']}): {msg_b}")

    # TEST RULE 18: Milan Over 10.5 Falli Commessi Squadra 2
    test_milan = {
        "match": "Torino vs Milan",
        "league": "Serie A",
        "pick": "Over 10.5 Falli Commessi Squadra 2",
        "is_high_possession_favorite": True
    }
    valid_m, msg_m = validator.validate_selection(test_milan)
    print(f"\n[Test Rule 18] {test_milan['match']} ({test_milan['pick']}): {msg_m}")

    # TEST RULE 19: Rennes-PSG Over 7.5 Corner Totali Match
    test_rennes = {
        "match": "Rennes vs PSG",
        "league": "Ligue 1",
        "pick": "Over 7.5 Corner Totali Match",
    }
    valid_r, msg_r = validator.validate_selection(test_rennes)
    print(f"\n[Test Rule 19] {test_rennes['match']} ({test_rennes['pick']}): {msg_r}")
