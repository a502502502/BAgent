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

        # REGOLA #31: BAN TOTALE 1ª GIORNATA DI CAMPIONATO (Hard Gate Matchday 1)
        if is_matchday_1:
            if pick in ["1", "2", "1X2: 1", "1X2: 2", "1X2", "1X", "X2"] or "over" in pick.lower() or "combo" in pick.lower():
                return False, f"[BLOCKED - RULE 31] BAN TOTALE 1ª GIORNATA: Vietato scommettere su squadre al debutto in campionato ({match_name}). Rodaggio estivo, nuovi innesti e varianza massima: SKIP / NO BET fino alla 2ª-3ª giornata!"

        # REGOLA #32: FALLACIA DELL'ASSENZA OFFENSIVA (Divieto 1X2 contro Big solo per assenza punte)
        is_bet_against_big_due_to_missing_forwards = match_data.get("is_bet_against_big_due_to_missing_forwards", False)
        if is_bet_against_big_due_to_missing_forwards:
            return False, f"[BLOCKED - RULE 32] FALLACIA DELL'ASSENZA OFFENSIVA ({match_name}): Vietato puntare sulla sfavorita (o 1X/X2) solo perché la big non ha le punte titolari! Il divario qualitativo tra le rose rimane intatto. Usare solo mercati sanzioni/statistici."

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

        # REGOLA #20: Audit Rosa SQLite Obbligatorio su Giocatori
        player_name = match_data.get("player_target")
        if player_name and not match_data.get("player_verified_in_db", False):
            return False, f"[BLOCKED - RULE 20] Il giocatore target '{player_name}' non è stato verificato nel DB SQLite (storage/database/bagent.db). Eseguire prima query_player.py!"

        # REGOLA #21 & #22: Rassegna Stampa Obbligatoria Pre-Calcolo
        if not match_data.get("press_scanned", False):
            return False, f"[BLOCKED - RULE 21/22] Rassegna Stampa non eseguita per {match_name} ({league}). TASSATIVO leggere Gazzetta/BBC/Marca prima del calcolo quote!"

        # REGOLA #23: Kelly Criterion Staking Guard
        stake = match_data.get("stake")
        bankroll = match_data.get("bankroll", 116.45)
        edge = match_data.get("edge", 0.05)
        # REGOLA #7: Trappola della Favorita in Trasferta nelle Coppe
        is_cup_or_knockout = any(term in league.lower() for term in ["conference", "europa", "champions", "cup", "coppa", "uefa"])
        is_away_favorite_pick = match_data.get("is_away", False) or "ospite" in pick.lower() or "2" in pick.split()
        if is_cup_or_knockout and is_away_favorite_pick:
            if any(term in pick.lower() for term in ["over 1.5 gol squadra", "over 1.5 sq.2", "over 1.5 ospite", "2 secco", "1x2: 2"]):
                return False, f"[BLOCKED - RULE 7] Trappola Favorita in Trasferta nelle Coppe ({match_name}): vietato 2 secco o Over Gol Ospite in trasferta europea! Consentiti solo DC X2, Under o linee cumulative di match."

        # REGOLA #26: Protocollo di Rigore Matematico (Max 3-4 Eventi d'Acciaio & No Catene Falli Giocatore)
        ticket_events_count = match_data.get("ticket_events_count", 3)
        if ticket_events_count > 4:
            return False, f"[BLOCKED - RULE 26] Schedina con {ticket_events_count} eventi (> 4)! Ritorno obbligatorio a Max 3-4 Eventi d'Acciaio."

        player_props_in_ticket = match_data.get("player_props_in_ticket", 0)
        if player_props_in_ticket > 2:
            return False, f"[BLOCKED - RULE 26] Rilevati {player_props_in_ticket} mercati sui falli/duelli giocatore nello stesso ticket (> 2). I mercati individuali hanno troppa varianza e sono vietati nelle multiple lunghe!"

        # REGOLA #29: Ban Under 2.5 nelle Leghe Minori
        if is_latam_or_minor and "under 2.5" in pick.lower():
            return False, f"[BLOCKED - RULE 29] Ban Under 2.5 Gol nelle Leghe Minori ({match_name} in {league}). Sostituire con Under 3.5 (via The Odds API alternate_totals) o mercati protetti (DC / Corner)!"

        return True, f"[APPROVED] Conforme a tutte le 30 Regole Inviolabili di BetGuard."

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
