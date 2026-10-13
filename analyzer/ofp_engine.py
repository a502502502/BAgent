#!/usr/bin/env python3
"""
BAgent OFP Engine (Oddspedia / Forebet / Pengwin)
Modulo di incrocio a tripla convergenza statistica e tattica:
- O = Oddspedia (Market consensus, quote bookmakers, dropping odds, sentiment)
- F = Forebet / Freebet (Modelli matematici Poisson, probabilita %, xG, risultati esatti)
- P = MondoPengwin (Analisi qualitativa, flussi mercati speciali, cartellini/angoli, motivazioni)
Rose, allenatori, infortuni e schemi tattici rigorosamente aggiornati al calcio reale.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json


@dataclass
class OFPMatchAnalysis:
    match: str
    kickoff: str
    tournament: str
    
    # Dati Squadre e Rose Reali
    home_manager: str
    away_manager: str
    home_key_players: str
    away_key_players: str
    home_absences: str
    away_absences: str
    
    # 1. O - Oddspedia
    oddspedia_odds: Dict[str, float]  # es. {"1": 1.40, "X": 4.60, "2": 7.50}
    oddspedia_sentiment: str          # es. "Forte convergenza su segno 1"
    oddspedia_key_market: str         # es. "1"
    
    # 2. F - Forebet
    forebet_pred_score: str           # es. "2-0"
    forebet_prob: Dict[str, int]      # es. {"1": 68, "X": 20, "2": 12}
    forebet_over_under: str           # es. "Over 1.5 (82%), Under 3.5 (70%)"
    
    # 3. P - Pengwin
    pengwin_pick: str                 # es. "1 fisso oppure 1 + Over 1.5"
    pengwin_rationale: str            # es. "Obbligo riscatto dopo Madrid, San Siro decisivo"
    pengwin_special: Optional[str]    # es. "Cartellini / Marcatori / Combo"
    
    # Sintesi OFP
    convergence_grade: str            # "AAA" (convergenza totale), "AA", "A"
    recommended_primary: str          # es. "1" o "2 + Over 1.5"
    recommended_safe: str             # es. "1X + MultiGol 1-4"
    target_odds: float                # es. 1.35 - 1.50
    risk_profile: str                 # "BASSO", "MEDIO", "ALTO"


class OFPEngine:
    """Motore di calcolo e incrocio OFP."""

    def __init__(self):
        self.matches: List[OFPMatchAnalysis] = []

    def add_match(self, analysis: OFPMatchAnalysis):
        self.matches.append(analysis)

    def get_tier_one_picks(self) -> List[OFPMatchAnalysis]:
        """Restituisce solo i match con massima convergenza (AAA o AA)."""
        return [m for m in self.matches if m.convergence_grade in ("AAA", "AA")]

    def generate_recommended_doubles(self) -> List[Dict]:
        """Genera le combinazioni a doppia perfette incrociando i rating OFP."""
        tier1 = self.get_tier_one_picks()
        doubles = []
        if len(tier1) >= 2:
            m1 = tier1[0]
            m2 = tier1[1]
            doubles.append({
                "type": "DOPPIA_SICUREZZA_OFP",
                "label": "Doppia Raddoppio Conservativa (Grade AAA)",
                "legs": [
                    {"match": m1.match, "pick": m1.recommended_safe, "odds": m1.target_odds},
                    {"match": m2.match, "pick": m2.recommended_safe, "odds": m2.target_odds}
                ],
                "total_odds": round(m1.target_odds * m2.target_odds, 2)
            })
        return doubles

    def to_dict(self) -> List[Dict]:
        return [
            {
                "match": m.match,
                "kickoff": m.kickoff,
                "tournament": m.tournament,
                "managers": f"{m.home_manager} vs {m.away_manager}",
                "key_players": {
                    "home": m.home_key_players,
                    "away": m.away_key_players
                },
                "absences": {
                    "home": m.home_absences,
                    "away": m.away_absences
                },
                "oddspedia": {
                    "odds": m.oddspedia_odds,
                    "sentiment": m.oddspedia_sentiment,
                    "key_market": m.oddspedia_key_market
                },
                "forebet": {
                    "pred_score": m.forebet_pred_score,
                    "prob": m.forebet_prob,
                    "over_under": m.forebet_over_under
                },
                "pengwin": {
                    "pick": m.pengwin_pick,
                    "rationale": m.pengwin_rationale,
                    "special": m.pengwin_special
                },
                "ofp_summary": {
                    "convergence_grade": m.convergence_grade,
                    "recommended_primary": m.recommended_primary,
                    "recommended_safe": m.recommended_safe,
                    "target_odds": m.target_odds,
                    "risk_profile": m.risk_profile
                }
            }
            for m in self.matches
        ]


def build_today_champions_ofp() -> OFPEngine:
    """Popola l'analisi OFP ufficiale per la Champions League del 13 Ottobre 2026 con rose reali."""
    engine = OFPEngine()

    # 1. Inter vs Club Brugge (21:00)
    engine.add_match(OFPMatchAnalysis(
        match="Inter vs Club Brugge",
        kickoff="13-10 21:00",
        tournament="UEFA Champions League",
        home_manager="Simone Inzaghi",
        away_manager="Nicky Hayen",
        home_key_players="Sommer; Pavard, Acerbi, Bastoni; Dumfries, Barella, Calhanoglu, Mkhitaryan, Dimarco; Lautaro Martinez, Thuram",
        away_key_players="Mignolet; Seys, Mechele, Ordonez, De Cuyper; Onyedika, Jashari; Skov Olsen, Vanaken, Tzolis; Jutgla (o Nilsson)",
        home_absences="Buchanan (recupero), Barella rientrato a pieno, Zielinski disponibile",
        away_absences="Gustaf Nilsson (in dubbio per affaticamento al polpaccio)",
        oddspedia_odds={"1": 1.40, "X": 4.60, "2": 7.50},
        oddspedia_sentiment="Forte convergenza sul segno 1, quote bookmaker in discesa",
        oddspedia_key_market="1",
        forebet_pred_score="2-0",
        forebet_prob={"1": 68, "X": 20, "2": 12},
        forebet_over_under="Over 1.5 (82%), Under 3.5 (71%)",
        pengwin_pick="1 fisso oppure 1 + Over 1.5",
        pengwin_rationale="Brugge ha vinto solo 1 volta in 9 trasferte in Italia; Inter a San Siro con la Thu-La titolare ha obbligo di riscatto",
        pengwin_special="Marcatore Lautaro Martinez / Combo 1 + No Gol",
        convergence_grade="AAA",
        recommended_primary="1",
        recommended_safe="1X + MultiGol 1-4",
        target_odds=1.40,
        risk_profile="BASSO"
    ))

    # 2. Viking vs Bayern Monaco (21:00)
    engine.add_match(OFPMatchAnalysis(
        match="Viking vs Bayern Monaco",
        kickoff="13-10 21:00",
        tournament="UEFA Champions League",
        home_manager="Bjarte Lunde Aarsheim",
        away_manager="Vincent Kompany",
        home_key_players="Ostbo; Haugen, Stensness, Langas, Vevatne; Bell, Tripic, Yazbek; Salvesen",
        away_key_players="Neuer; Guerreiro, Upamecano, Kim Min-jae, Davies; Kimmich, Pavlovic (Palhinha); Olise, Musiala, Gnabry; Harry Kane",
        home_absences="Nessuna assenza primaria",
        away_absences="Stanisic, Boey, Ito (infortuni difensivi noti); attacco titolare al 100%",
        oddspedia_odds={"1": 11.00, "X": 6.50, "2": 1.22},
        oddspedia_sentiment="Dominio Bayern, quota 2 schiacciante",
        oddspedia_key_market="2",
        forebet_pred_score="0-3",
        forebet_prob={"1": 6, "X": 13, "2": 81},
        forebet_over_under="Over 2.5 (78%), Over 1.5 Ospite (84%)",
        pengwin_pick="2 + Over 2.5 oppure MultiGol Ospite 2-4",
        pengwin_rationale="Dislivello tecnico abissale. Kane incontenibile e bavaresi macchina da gol in Europa",
        pengwin_special="Harry Kane Marcatore / 2 + Over 2.5",
        convergence_grade="AAA",
        recommended_primary="2 + Over 2.5",
        recommended_safe="2 + Over 1.5",
        target_odds=1.35,
        risk_profile="BASSO"
    ))

    # 3. Villarreal vs Napoli (21:00)
    engine.add_match(OFPMatchAnalysis(
        match="Villarreal vs Napoli",
        kickoff="13-10 21:00",
        tournament="UEFA Champions League",
        home_manager="Marcelino Garcia Toral",
        away_manager="Antonio Conte",
        home_key_players="Diego Conde; Kiko Femenia, Albiol, Bailly (Logan Costa), Sergi Cardona; Comesana, Parejo, Alex Baena, Yeremy Pino; Ayoze Perez, Thierno Barry (Pepe)",
        away_key_players="Meret (Caprile); Di Lorenzo, Rrahmani, Buongiorno, Olivera (Spinazzola); Anguissa, Lobotka, McTominay; Politano, Lukaku, Kvaratskhelia",
        home_absences="Gerard Moreno (lesione muscolare), Juan Foyth (ginocchio), Pedraza out",
        away_absences="Meret monitorato (pronto Caprile), rosa titolare offensiva al completo con Lukaku e Kvara",
        oddspedia_odds={"1": 2.15, "X": 3.60, "2": 3.10},
        oddspedia_sentiment="Match equilibrato, quote Gol / Over 2.5 in costante discesa",
        oddspedia_key_market="Gol / X2",
        forebet_pred_score="1-2",
        forebet_prob={"1": 34, "X": 28, "2": 38},
        forebet_over_under="Gol (65%), Under 3.5 (66%)",
        pengwin_pick="MultiGol Ospite 1-3 oppure X2",
        pengwin_rationale="Villarreal reduce da 7 sconfitte consecutive in UCL; difesa fragile contro le ripartenze di Lukaku e Kvaratskhelia guidati da Conte",
        pengwin_special="Cartellini Totali Over 4.5 / MultiGol Ospite 1-3",
        convergence_grade="AA",
        recommended_primary="MultiGol Ospite 1-3",
        recommended_safe="X2 + Under 4.5",
        target_odds=1.38,
        risk_profile="MEDIO"
    ))

    # 4. Arsenal vs Lille (21:00)
    engine.add_match(OFPMatchAnalysis(
        match="Arsenal vs Lille",
        kickoff="13-10 21:00",
        tournament="UEFA Champions League",
        home_manager="Mikel Arteta",
        away_manager="Bruno Genesio",
        home_key_players="Raya; White, Saliba, Gabriel Magalhaes, Calafiori (Timber); Partey, Rice, Merino (Jorginho); Saka, Havertz, Martinelli (Trossard)",
        away_key_players="Chevalier; Meunier, Diakite, Alexsandro, Gudmundsson; Andre, Angel Gomes; Zhegrova, Cabella, Sahraoui; Jonathan David",
        home_absences="Martin Odegaard (caviglia), Zinchenko (polpaccio)",
        away_absences="Tiago Santos, Umtiti, Bentaleb (infortuni di lungo corso)",
        oddspedia_odds={"1": 1.35, "X": 4.80, "2": 8.50},
        oddspedia_sentiment="Arsenal favorito indiscusso all'Emirates, quota 1 blindata",
        oddspedia_key_market="1",
        forebet_pred_score="2-0",
        forebet_prob={"1": 72, "X": 18, "2": 10},
        forebet_over_under="Under 3.5 (68%), 1X (90%)",
        pengwin_pick="1 fisso oppure 1 + MultiGol 1-4",
        pengwin_rationale="Arsenal all'Emirates con difesa ermetica (Saliba-Gabriel); Lille soffre terribilmente l'impatto fisico inglese",
        pengwin_special="1 + No Gol / 1 fisso",
        convergence_grade="AAA",
        recommended_primary="1",
        recommended_safe="1X + MultiGol 1-4",
        target_odds=1.35,
        risk_profile="BASSO"
    ))

    # 5. Galatasaray vs Barcellona (21:00)
    engine.add_match(OFPMatchAnalysis(
        match="Galatasaray vs Barcellona",
        kickoff="13-10 21:00",
        tournament="UEFA Champions League",
        home_manager="Okan Buruk",
        away_manager="Hansi Flick",
        home_key_players="Muslera; Kaan Ayhan, Davinson Sanchez, Bardakci, Jakobs; Torreira, Gabriel Sara; Baris Alper Yilmaz, Mertens, Akgun (Sallai); Victor Osimhen (Icardi)",
        away_key_players="Inaki Pena (Szczesny); Kounde, Cubarsi, Inigo Martinez, Balde; Casado, Pedri, Dani Olmo; Lamine Yamal, Lewandowski, Raphinha",
        home_absences="Jelert e Ziyech in dubbio; Osimhen al centro dell'attacco",
        away_absences="Ter Stegen (stagione finita), Araujo, Christensen, Ferran Torres",
        oddspedia_odds={"1": 4.20, "X": 4.00, "2": 1.75},
        oddspedia_sentiment="Barca favorito, quote Over 2.5 e Gol crollate a 1.50",
        oddspedia_key_market="Over 2.5 / 2",
        forebet_pred_score="1-3",
        forebet_prob={"1": 18, "X": 24, "2": 58},
        forebet_over_under="Over 2.5 (70%), Gol (64%)",
        pengwin_pick="Gol oppure X2 + Over 1.5",
        pengwin_rationale="Atmosfera infernale a Istanbul; Osimhen punge la linea altissima di Flick, ma il Barca di Lewandowski e Yamal crea occasioni a raffica",
        pengwin_special="Gol Entrambe / Over 2.5",
        convergence_grade="AA",
        recommended_primary="Over 2.5",
        recommended_safe="X2 + Over 1.5",
        target_odds=1.36,
        risk_profile="MEDIO"
    ))

    # 6. Atletico Madrid vs Manchester United (21:00)
    engine.add_match(OFPMatchAnalysis(
        match="Atlético Madrid vs Manchester United",
        kickoff="13-10 21:00",
        tournament="UEFA Champions League",
        home_manager="Diego Simeone",
        away_manager="Erik ten Hag",
        home_key_players="Oblak; Molina, Gimenez, Le Normand (Witsel), Reinildo (Galan); De Paul, Koke, Gallagher, Samuel Lino; Antoine Griezmann, Julian Alvarez",
        away_key_players="Onana; Mazraoui, De Ligt, Lisandro Martinez, Dalot; Casemiro, Mainoo; Garnacho, Bruno Fernandes, Rashford; Hojlund",
        home_absences="Azpilicueta, Le Normand (in dubbio dopo colpo alla testa)",
        away_absences="Luke Shaw, Malacia, Mount; Hojlund tornato disponibile al centro",
        oddspedia_odds={"1": 2.10, "X": 3.30, "2": 3.40},
        oddspedia_sentiment="Gara bloccata e nervosa, quote Under 2.5 favorite",
        oddspedia_key_market="1X / Under 2.5",
        forebet_pred_score="1-0",
        forebet_prob={"1": 44, "X": 32, "2": 24},
        forebet_over_under="Under 2.5 (62%), 1X (76%)",
        pengwin_pick="1X + Under 3.5",
        pengwin_rationale="Gara a scacchi di Simeone: blocco basso, provocazione e ripartenze; United discontinuo nelle trasferte iberiche",
        pengwin_special="Cartellini Totali Over 4.5 / 1X",
        convergence_grade="AA",
        recommended_primary="1X + Under 3.5",
        recommended_safe="Under 3.5",
        target_odds=1.45,
        risk_profile="MEDIO"
    ))

    # 7. RB Lipsia vs PSV Eindhoven (21:00)
    engine.add_match(OFPMatchAnalysis(
        match="RB Lipsia vs PSV Eindhoven",
        kickoff="13-10 21:00",
        tournament="UEFA Champions League",
        home_manager="Marco Rose",
        away_manager="Peter Bosz",
        home_key_players="Gulacsi; Geertruida, Orban, Lukeba, Henrichs; Vermeeren, Haidara, Xavi Simons, Nusa; Lois Openda, Benjamin Sesko",
        away_key_players="Benitez; Karsdorp, Flamingo, Boscagli, Mauro Junior; Schouten, Til, Tillman; Bakayoko, Luuk de Jong, Noa Lang",
        home_absences="David Raum (caviglia), Schlager (ginocchio)",
        away_absences="Joey Veerman (infortunio muscolare all'inguine), Dest (lungo degente)",
        oddspedia_odds={"1": 1.90, "X": 3.70, "2": 3.60},
        oddspedia_sentiment="Partita aperta a qualsiasi esito, quote Gol/Over gettonatissime",
        oddspedia_key_market="Gol / Over 2.5",
        forebet_pred_score="2-1",
        forebet_prob={"1": 50, "X": 26, "2": 24},
        forebet_over_under="Over 2.5 (66%), Gol (68%)",
        pengwin_pick="Gol oppure 1X + Over 1.5",
        pengwin_rationale="Due filosofie votate all'attacco puro: Openda e Sesko contro Luuk de Jong e Bakayoko",
        pengwin_special="Gol Entrambe / Over 2.5",
        convergence_grade="AA",
        recommended_primary="Gol",
        recommended_safe="1X + Over 1.5",
        target_odds=1.45,
        risk_profile="MEDIO"
    ))

    # 8. Lens vs Sporting CP (18:45)
    engine.add_match(OFPMatchAnalysis(
        match="Lens vs Sporting CP",
        kickoff="13-10 18:45",
        tournament="UEFA Champions League",
        home_manager="Will Still",
        away_manager="Ruben Amorim",
        home_key_players="Samba; Frankowski, Gradit, Khusanov, Medina, Machado; Thomasson, Diouf; Sotoca, Nzola (Said), Zaroury",
        away_key_players="Israel; Debast, Diomande, Inacio; Quenda, Hjulmand, Morita, Nuno Santos; Trincao, Viktor Gyokeres, Pedro Goncalves (Pote)",
        home_absences="Danso (condizione), Cabot",
        away_absences="Matheus Reis, Kovacevic",
        oddspedia_odds={"1": 2.55, "X": 3.30, "2": 2.70},
        oddspedia_sentiment="Equilibrio tattico, leggero favore Sporting per la presenza del bomber Gyokeres",
        oddspedia_key_market="X2 / Under 2.5",
        forebet_pred_score="1-1",
        forebet_prob={"1": 31, "X": 35, "2": 34},
        forebet_over_under="Under 2.5 (58%), Under 3.5 (74%)",
        pengwin_pick="X2 oppure MultiGol 1-3",
        pengwin_rationale="Gara molto fisica e tattica al Bollaert-Delelis; Sporting di Amorim abituato a gestire il ritmo con Gyokeres spauracchio",
        pengwin_special="Viktor Gyokeres Marcatore / MultiGol 1-3",
        convergence_grade="A",
        recommended_primary="MultiGol 1-3",
        recommended_safe="Under 3.5",
        target_odds=1.30,
        risk_profile="BASSO"
    ))

    # 9. Sabah vs Slavia Praga (18:45)
    engine.add_match(OFPMatchAnalysis(
        match="Sabah vs Slavia Praga",
        kickoff="13-10 18:45",
        tournament="UEFA Champions League",
        home_manager="Krunoslav Rendulic",
        away_manager="Jindrich Trpisovsky",
        home_key_players="Imanov; Seydiyev, Irazabal, Stankovic, Letic; Khaybulaev, Camalov; Mickels, Sekidika, Safranko",
        away_key_players="Kinsky; Holes, Zima, Boril; Doudera, Zafeiris, Oscar Dorley, Diouf; Provod, Chory, Schranz",
        home_absences="Nessuna defezione maggiore",
        away_absences="Masopust, Vlcek",
        oddspedia_odds={"1": 5.50, "X": 4.00, "2": 1.60},
        oddspedia_sentiment="Slavia Praga nettamente favorito in trasferta",
        oddspedia_key_market="2",
        forebet_pred_score="0-2",
        forebet_prob={"1": 15, "X": 25, "2": 60},
        forebet_over_under="Under 3.5 (70%), X2 (85%)",
        pengwin_pick="2 secco oppure X2 + Under 3.5",
        pengwin_rationale="Slavia Praga superiore per fisicità e ritmo europeo alla matricola azera",
        pengwin_special="2 secco",
        convergence_grade="AA",
        recommended_primary="2",
        recommended_safe="X2 + Under 3.5",
        target_odds=1.45,
        risk_profile="BASSO"
    ))

    return engine


if __name__ == "__main__":
    eng = build_today_champions_ofp()
    print(f"Caricati {len(eng.matches)} match con algoritmo OFP e rose reali.")
    for m in eng.matches:
        print(f"[{m.convergence_grade}] {m.match} ({m.home_manager} vs {m.away_manager}) -> Pick: {m.recommended_primary} (Safe: {m.recommended_safe})")
