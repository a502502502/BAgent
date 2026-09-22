#!/usr/bin/env python3
"""
scripts/live_telegram_scoreboard.py — Sentinella Telegram Live Real-Time Multi-Ticket
Monitora in tempo reale tutti i match delle 4 schedine attive di oggi (Lunedì 7 Settembre 2026):
Ticket #56 (Pomeridiana Over), Ticket #57 (Sanzioni & Falli), Ticket #54 (Corner & Multigol), Ticket #55 (Combo & Doppie Chance).

Gestione robusta:
- Distinzione tra Gol Reale e Gol Annullato (VAR / correzione feed)
- Nessuna notifica duplicata o incongruente (es. "Gol 0-0")
- Rilevamento marcatore preciso
- Tracciamento milestone univoco (Corner, Cartellini, Falli subiti Zaccagni/Oyarzabal)
- Aggiornamento continuo avanzamento ticket
"""

from __future__ import annotations
import os
import sys
import time
import requests
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from services.football.external.collector import FootballExternalCollector

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def send_telegram(msg: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[TELEGRAM SKIPPED] Mancano token o chat_id", flush=True)
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=10,
        )
        if not r.ok:
            print(f"[TELEGRAM ERROR] {r.status_code}: {r.text[:200]}", flush=True)
            return False
        return True
    except Exception as e:
        print(f"[TELEGRAM EXCEPTION] {e}", flush=True)
        return False

# Struttura delle 4 Schedine e delle 9 Partite
FIXTURES_CONFIG = {
    1629414: {
        "label": "Göztepe U19 vs Gaziantep U19",
        "competition": "🇹🇷 Turchia U19 Elit A",
        "time_cest": "15:00",
        "bets": [
            {
                "ticket": "#56",
                "ticket_name": "Pomeridiana Over",
                "market": "Over 2.5 Gol",
                "odd": 1.52,
                "type": "over_goals",
                "threshold": 2.5
            }
        ]
    },
    1637280: {
        "label": "Corea del Nord U20 D vs Portogallo U20 D",
        "competition": "🌍 Mondiale U20 Donne",
        "time_cest": "15:00",
        "bets": [
            {
                "ticket": "#56",
                "ticket_name": "Pomeridiana Over",
                "market": "Over 2.5 Gol",
                "odd": 1.38,
                "type": "over_goals",
                "threshold": 2.5
            }
        ]
    },
    1531094: {
        "label": "Metalourg Bekabad vs Pakhtakor II",
        "competition": "🇺🇿 Uzbekistan Pro Liga",
        "time_cest": "15:30",
        "bets": [
            {
                "ticket": "#56",
                "ticket_name": "Pomeridiana Over",
                "market": "Over 3.5 Gol",
                "odd": 1.97,
                "type": "over_goals",
                "threshold": 3.5
            }
        ]
    },
    1550109: {
        "label": "Cagliari vs Lecce",
        "competition": "🇮🇹 Serie A",
        "time_cest": "18:30",
        "bets": [
            {
                "ticket": "#57",
                "ticket_name": "Sanzioni & Falli",
                "market": "Under 3.5 Gol",
                "odd": 1.22,
                "type": "under_goals",
                "threshold": 3.5
            }
        ]
    },
    1570368: {
        "label": "Getafe vs Celta Vigo",
        "competition": "🇪🇸 LaLiga",
        "time_cest": "19:00",
        "bets": [
            {
                "ticket": "#54",
                "ticket_name": "Corner & Multigol",
                "market": "MultiGol 0-1 Casa: SI",
                "odd": 1.32,
                "type": "home_multigoal_0_1"
            },
            {
                "ticket": "#57",
                "ticket_name": "Sanzioni & Falli",
                "market": "Over 4.5 Cartellini",
                "odd": 1.49,
                "type": "over_cards",
                "threshold": 4.5
            }
        ]
    },
    1549015: {
        "label": "FC Midtjylland vs FC Nordsjaelland",
        "competition": "🇩🇰 Danimarca Superligaen",
        "time_cest": "19:00",
        "bets": [
            {
                "ticket": "#54",
                "ticket_name": "Corner & Multigol",
                "market": "Over 8.5 Corner (esc. TS)",
                "odd": 1.39,
                "type": "over_corners_total",
                "threshold": 8.5
            }
        ]
    },
    1601520: {
        "label": "Palermo vs Sampdoria",
        "competition": "🇮🇹 Serie B",
        "time_cest": "20:30",
        "bets": [
            {
                "ticket": "#54",
                "ticket_name": "Corner & Multigol",
                "market": "Over 4.5 Corner Squadra 1 (Palermo)",
                "odd": 1.48,
                "type": "home_corners",
                "threshold": 4.5
            },
            {
                "ticket": "#55",
                "ticket_name": "Combo & Valore",
                "market": "Doppia Chance 1X",
                "odd": 1.17,
                "type": "double_chance_1x"
            }
        ]
    },
    1550116: {
        "label": "Udinese vs Lazio",
        "competition": "🇮🇹 Serie A",
        "time_cest": "20:45",
        "bets": [
            {
                "ticket": "#55",
                "ticket_name": "Combo & Valore",
                "market": "X2 + Under 3.5 Gol",
                "odd": 1.80,
                "type": "combo_x2_u35"
            },
            {
                "ticket": "#57",
                "ticket_name": "Sanzioni & Falli",
                "market": "Zaccagni Over 1.5 Falli Subiti",
                "odd": 1.20,
                "type": "player_fouls_drawn",
                "player_name": "Zaccagni",
                "threshold": 1.5
            },
            {
                "ticket": "#58",
                "ticket_name": "Tripla d'Acciaio Live",
                "market": "Doppia Chance X2",
                "odd": 1.25,
                "type": "double_chance_x2"
            }
        ]
    },
    1570366: {
        "label": "Elche vs Real Sociedad",
        "competition": "🇪🇸 LaLiga",
        "time_cest": "21:30",
        "bets": [
            {
                "ticket": "#55",
                "ticket_name": "Combo & Valore",
                "market": "Doppia Chance X2",
                "odd": 1.32,
                "type": "double_chance_x2"
            },
            {
                "ticket": "#57",
                "ticket_name": "Sanzioni & Falli",
                "market": "Oyarzabal Over 1.5 Falli Subiti",
                "odd": 1.75,
                "type": "player_fouls_drawn",
                "player_name": "Oyarzabal",
                "threshold": 1.5
            },
            {
                "ticket": "#58",
                "ticket_name": "Tripla d'Acciaio Live",
                "market": "Doppia Chance X2",
                "odd": 1.12,
                "type": "double_chance_x2"
            }
        ]
    },
    1575483: {
        "label": "Estoril vs Arouca",
        "competition": "🇵🇹 Portogallo Primeira Liga",
        "time_cest": "21:15",
        "bets": [
            {
                "ticket": "#58",
                "ticket_name": "Tripla d'Acciaio Live",
                "market": "Under 2.5 Gol",
                "odd": 1.40,
                "type": "under_goals",
                "threshold": 2.5
            }
        ]
    },
    1634048: {
        "label": "Corinthians Donne vs Cruzeiro Donne",
        "competition": "🇧🇷 Brasileirão Playoff Femminile",
        "time_cest": "22:00",
        "bets": [
            {
                "ticket": "#59",
                "ticket_name": "Doppia d'Acciaio Recupero",
                "market": "1X2: 1",
                "odd": 1.42,
                "type": "match_winner_1"
            }
        ]
    },
    1498787: {
        "label": "Nueva Chicago vs Quilmes",
        "competition": "🇦🇷 Argentina Primera Nacional",
        "time_cest": "22:00",
        "bets": [
            {
                "ticket": "#59",
                "ticket_name": "Doppia d'Acciaio Recupero",
                "market": "Under 2.5 Gol",
                "odd": 1.42,
                "type": "under_goals",
                "threshold": 2.5
            }
        ]
    },
    1631996: {
        "label": "Cerro Porteño vs Nacional Asunción",
        "competition": "🇵🇾 Paraguay Division Profesional",
        "time_cest": "23:30",
        "bets": [
            {
                "ticket": "#60",
                "ticket_name": "Corazzata Notturna",
                "market": "Doppia Chance 1X",
                "odd": 1.30,
                "type": "double_chance_1x"
            }
        ]
    },
    1493108: {
        "label": "Barracas Central vs Argentinos Jrs",
        "competition": "🇦🇷 Argentina Liga Profesional",
        "time_cest": "00:00",
        "bets": [
            {
                "ticket": "#60",
                "ticket_name": "Corazzata Notturna",
                "market": "Doppia Chance X2",
                "odd": 1.21,
                "type": "double_chance_x2"
            },
            {
                "ticket": "#61",
                "ticket_name": "Bomba Alta Quota",
                "market": "1X2: 2",
                "odd": 2.10,
                "type": "match_winner_2"
            }
        ]
    },
    1492369: {
        "label": "Vitória vs Grêmio",
        "competition": "🇧🇷 Brasileirão Serie A",
        "time_cest": "01:00",
        "bets": [
            {
                "ticket": "#60",
                "ticket_name": "Corazzata Notturna",
                "market": "Doppia Chance 1X",
                "odd": 1.30,
                "type": "double_chance_1x"
            },
            {
                "ticket": "#61",
                "ticket_name": "Bomba Alta Quota",
                "market": "Doppia Chance 1X",
                "odd": 1.32,
                "type": "double_chance_1x"
            }
        ]
    },
    1638141: {
        "label": "Carabobo vs Estudiantes de Mérida",
        "competition": "🇻🇪 Venezuela Primera División",
        "time_cest": "00:00",
        "bets": [
            {
                "ticket": "#61",
                "ticket_name": "Bomba Alta Quota",
                "market": "1X2: 1",
                "odd": 1.48,
                "type": "match_winner_1"
            }
        ]
    },
    1607188: {
        "label": "Atlético Nacional vs Deportivo Cali",
        "competition": "🇨🇴 Colombia Copa Colombia",
        "time_cest": "03:15",
        "bets": [
            {
                "ticket": "#61",
                "ticket_name": "Bomba Alta Quota",
                "market": "1X2: 1",
                "odd": 1.42,
                "type": "match_winner_1"
            }
        ]
    }
}

TICKETS_SUMMARY = {
    "#56": {"name": "Pomeridiana Over", "stake": 37.0, "total_odd": 4.13, "pot_win": 152.89, "total_legs": 3},
    "#54": {"name": "Corner & Multigol", "stake": 30.0, "total_odd": 2.72, "pot_win": 81.46, "total_legs": 3},
    "#55": {"name": "Combo & Valore", "stake": 25.0, "total_odd": 2.78, "pot_win": 69.49, "total_legs": 3},
    "#57": {"name": "Sanzioni & Falli", "stake": 30.0, "total_odd": 3.82, "pot_win": 114.52, "total_legs": 4},
    "#58": {"name": "Tripla d'Acciaio Live", "stake": 50.0, "total_odd": 1.96, "pot_win": 98.00, "total_legs": 3},
    "#59": {"name": "Doppia d'Acciaio Recupero", "stake": 30.0, "total_odd": 2.02, "pot_win": 60.49, "total_legs": 2},
    "#60": {"name": "Corazzata Notturna", "stake": 40.0, "total_odd": 2.06, "pot_win": 82.42, "total_legs": 3},
    "#61": {"name": "Bomba Alta Quota", "stake": 30.0, "total_odd": 6.00, "pot_win": 180.01, "total_legs": 4},
}

class LiveTelegramScoreboard:
    def __init__(self):
        self.collector = FootballExternalCollector()
        self.match_states: dict[int, dict] = {}
        self.seen_goal_events: set[tuple] = set()
        self.notified_milestones: set[tuple] = set()
        self.legs_won: dict[str, set[int]] = {"#56": set(), "#54": set(), "#55": set(), "#57": set(), "#58": set(), "#59": set(), "#60": set(), "#61": set()}
        self.notified_tickets_won: set[str] = set()
        self._init_states()

    def _init_states(self):
        for fid, cfg in FIXTURES_CONFIG.items():
            self.match_states[fid] = {
                "status": "NS",
                "elapsed": 0,
                "gh": 0,
                "ga": 0,
                "home_name": "",
                "away_name": "",
                "home_corners": 0,
                "away_corners": 0,
                "cards": 0,
                "player_fouls": {},
                "initialized": False
            }

    def format_bet_impact(self, fid: int, gh: int, ga: int, elapsed: int) -> list[str]:
        cfg = FIXTURES_CONFIG[fid]
        lines = []
        tot_goals = (gh or 0) + (ga or 0)
        
        for bet in cfg["bets"]:
            t_id = bet["ticket"]
            b_type = bet["type"]
            m_label = bet["market"]
            
            if b_type == "over_goals":
                thresh = bet["threshold"]
                needed = int(thresh + 0.5)
                if tot_goals >= needed:
                    self.legs_won[t_id].add(fid)
                    lines.append(f"• <b>Ticket {t_id}</b> ({m_label}): <b>✅ OBIETTIVO RAGGIUNTO!</b> ({tot_goals} gol)")
                else:
                    self.legs_won[t_id].discard(fid)
                    remain = needed - tot_goals
                    lines.append(f"• <b>Ticket {t_id}</b> ({m_label}): In corsa ({tot_goals}/{needed} gol — ne mancano {remain})")

            elif b_type == "under_goals":
                thresh = bet["threshold"]
                max_allowed = int(thresh)
                if tot_goals > max_allowed:
                    self.legs_won[t_id].discard(fid)
                    lines.append(f"• <b>Ticket {t_id}</b> ({m_label}): ❌ Sforata soglia ({tot_goals} gol)")
                else:
                    lines.append(f"• <b>Ticket {t_id}</b> ({m_label}): 🛡️ Al sicuro ({tot_goals}/{max_allowed} gol max)")

            elif b_type == "home_multigoal_0_1":
                if gh > 1:
                    self.legs_won[t_id].discard(fid)
                    lines.append(f"• <b>Ticket {t_id}</b> ({m_label}): ❌ Casa ha segnato 2+ gol ({gh})")
                else:
                    lines.append(f"• <b>Ticket {t_id}</b> ({m_label}): 🛡️ Al sicuro (Casa {gh} gol, max 1)")

            elif b_type == "double_chance_1x":
                curr = "1" if gh > ga else ("X" if gh == ga else "2")
                res_ok = gh >= ga
                tag = "🟢 FAVOREVOLE" if res_ok else "⚠️ SOTTO"
                lines.append(f"• <b>Ticket {t_id}</b> ({m_label}): {tag} (Parziale: {curr})")

            elif b_type == "double_chance_x2":
                curr = "2" if ga > gh else ("X" if gh == ga else "1")
                res_ok = ga >= gh
                tag = "🟢 FAVOREVOLE" if res_ok else "⚠️ SOTTO"
                lines.append(f"• <b>Ticket {t_id}</b> ({m_label}): {tag} (Parziale: {curr})")

            elif b_type == "combo_x2_u35":
                res_ok = ga >= gh and tot_goals <= 3
                tag = "🟢 FAVOREVOLE" if res_ok else "⚠️ A RISCHIO"
                lines.append(f"• <b>Ticket {t_id}</b> ({m_label}): {tag} (Tot. Gol: {tot_goals}/3)")

            elif b_type == "match_winner_1":
                curr = "1" if gh > ga else ("X" if gh == ga else "2")
                res_ok = gh > ga
                tag = "🟢 IN VANTAGGIO" if res_ok else ("⚖️ IN PARITÀ" if gh == ga else "⚠️ SOTTO")
                lines.append(f"• <b>Ticket {t_id}</b> ({m_label}): {tag} (Parziale: {curr})")

        return lines

    def check_full_tickets(self):
        for t_id, info in TICKETS_SUMMARY.items():
            if t_id in self.notified_tickets_won:
                continue
            if len(self.legs_won[t_id]) == info["total_legs"]:
                self.notified_tickets_won.add(t_id)
                msg = (
                    f"🎉🎉 <b>CASSAAAA! TICKET {t_id} PRESO AL 100%!</b> 🎉🎉\n\n"
                    f"👑 <b>{info['name']}</b> (@{info['total_odd']:.2f})\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💰 <b>Stake Giocato</b>: {info['stake']:.2f} €\n"
                    f"🏆 <b>INCASSO A CASSA</b>: <b>{info['pot_win']:.2f} €</b>\n"
                    f"📈 <b>Profitto Netto</b>: <b>+{info['pot_win'] - info['stake']:.2f} €</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🚀 <i>BAgent Quantitative Engine — Pronostico Impeccabile!</i>"
                )
                send_telegram(msg)

    def process_fixture_data(self, f: dict):
        fid = f["fixture"]["id"]
        cfg = FIXTURES_CONFIG.get(fid)
        if not cfg:
            return

        st = self.match_states[fid]
        new_status = f["fixture"]["status"]["short"]
        elapsed = f["fixture"]["status"]["elapsed"] or 0
        gh = f["goals"]["home"] if f["goals"]["home"] is not None else 0
        ga = f["goals"]["away"] if f["goals"]["away"] is not None else 0
        home = f["teams"]["home"]["name"]
        away = f["teams"]["away"]["name"]

        st["home_name"] = home
        st["away_name"] = away

        # Prima sincronizzazione dello stato (silenziosa se il match è già iniziato)
        if not st["initialized"]:
            st["initialized"] = True
            st["status"] = new_status
            st["elapsed"] = elapsed
            st["gh"] = gh
            st["ga"] = ga
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Sincronizzato {home} vs {away}: {gh}-{ga} [{new_status} {elapsed}']", flush=True)
            return

        # 1. Fischio d'inizio (se passa da NS a 1H/LIVE)
        if st["status"] == "NS" and new_status in ("1H", "LIVE", "1T"):
            st["status"] = new_status
            st["gh"] = gh
            st["ga"] = ga
            st["elapsed"] = elapsed or 1
            msg = (
                f"⏱️ <b>FISCHIO D'INIZIO!</b>\n\n"
                f"{cfg['competition']}\n"
                f"⚽ <b>{home} vs {away}</b> (1')\n"
                f"Risultato iniziale: 0 - 0\n\n"
                f"📋 <b>Selezioni collegate:</b>\n" +
                "\n".join([f"• Ticket {b['ticket']} ➔ <b>{b['market']}</b> (@{b['odd']:.2f})" for b in cfg["bets"]])
            )
            send_telegram(msg)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Kickoff notified: {home} vs {away}", flush=True)
            return

        old_tot = st["gh"] + st["ga"]
        new_tot = gh + ga

        # 2A. VERO GOL SEGNATO (Il totale gol è aumentato!)
        if new_tot > old_tot and new_status in ("1H", "2H", "HT", "ET", "LIVE"):
            st["gh"] = gh
            st["ga"] = ga
            st["elapsed"] = elapsed

            # Trova marcatore reale
            events = f.get("events", [])
            scorer_str = ""
            for ev in reversed(events):
                if ev.get("type") == "Goal":
                    p_name = ev.get("player", {}).get("name", "")
                    t_name = ev.get("team", {}).get("name", "")
                    m = ev.get("time", {}).get("elapsed", elapsed)
                    detail = ev.get("detail", "Gol")
                    ev_key = (fid, m, p_name, t_name)
                    if ev_key not in self.seen_goal_events:
                        self.seen_goal_events.add(ev_key)
                        scorer_str = f"👤 Marcatore: <b>{p_name}</b> ({t_name}, {m}') [{detail}]"
                        break

            impact_lines = self.format_bet_impact(fid, gh, ga, elapsed)

            msg = (
                f"⚽ <b>GOOOOL! CAMBIO RISULTATO!</b>\n\n"
                f"{cfg['competition']}\n"
                f"🔥 <b>{home} {gh} - {ga} {away}</b> ({elapsed}')\n"
            )
            if scorer_str:
                msg += f"{scorer_str}\n"
            msg += f"\n📊 <b>Impatto sulle Schedine:</b>\n" + "\n".join(impact_lines)

            send_telegram(msg)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Goal notified: {home} {gh}-{ga} {away}", flush=True)

        # 2B. GOL ANNULLATO / RETTIFICA VAR (Il totale gol è diminuito!)
        elif new_tot < old_tot and new_status in ("1H", "2H", "HT", "ET", "LIVE"):
            st["gh"] = gh
            st["ga"] = ga
            st["elapsed"] = elapsed

            impact_lines = self.format_bet_impact(fid, gh, ga, elapsed)

            msg = (
                f"❌ <b>VAR / RETTIFICA: GOL ANNULLATO!</b>\n\n"
                f"{cfg['competition']}\n"
                f"⚠️ Decisione arbitrale o correzione ufficiale: gol revocato!\n"
                f"⚖️ Il punteggio di <b>{home} vs {away}</b> torna su: <b>{gh} - {ga}</b> ({elapsed}')\n\n"
                f"📊 <b>Nuovo Stato Schedine:</b>\n" + "\n".join(impact_lines)
            )
            send_telegram(msg)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Disallowed goal notified: {home} {gh}-{ga} {away}", flush=True)

        # 3. Fine Primo Tempo (Intervallo)
        if st["status"] != "HT" and new_status == "HT":
            st["status"] = "HT"
            impact_lines = self.format_bet_impact(fid, gh, ga, 45)
            msg = (
                f"⏸️ <b>FINE PRIMO TEMPO (INTERVALLO)</b>\n\n"
                f"{cfg['competition']}\n"
                f"⚖️ <b>{home} {gh} - {ga} {away}</b> (45')\n\n"
                f"📊 <b>Riepilogo Schedine:</b>\n" + "\n".join(impact_lines)
            )
            send_telegram(msg)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] HT notified: {home} vs {away}", flush=True)

        # 4. Risultato Finale Definitivo
        if st["status"] != "FT" and new_status in ("FT", "AET", "PEN"):
            st["status"] = "FT"
            tot_goals = gh + ga
            final_lines = []
            for bet in cfg["bets"]:
                t_id = bet["ticket"]
                b_type = bet["type"]
                m_label = bet["market"]
                if b_type == "over_goals":
                    if tot_goals > bet["threshold"]:
                        self.legs_won[t_id].add(fid)
                        final_lines.append(f"• Ticket {t_id} ({m_label}): <b>✅ VINTO</b> ({tot_goals} gol)")
                    else:
                        final_lines.append(f"• Ticket {t_id} ({m_label}): <b>❌ PERSO</b> ({tot_goals} gol)")
                elif b_type == "under_goals":
                    if tot_goals < bet["threshold"]:
                        self.legs_won[t_id].add(fid)
                        final_lines.append(f"• Ticket {t_id} ({m_label}): <b>✅ VINTO</b> ({tot_goals} gol)")
                    else:
                        final_lines.append(f"• Ticket {t_id} ({m_label}): <b>❌ PERSO</b> ({tot_goals} gol)")
                elif b_type == "home_multigoal_0_1":
                    if gh <= 1:
                        self.legs_won[t_id].add(fid)
                        final_lines.append(f"• Ticket {t_id} ({m_label}): <b>✅ VINTO</b> ({gh} gol casa)")
                    else:
                        final_lines.append(f"• Ticket {t_id} ({m_label}): <b>❌ PERSO</b> ({gh} gol casa)")
                elif b_type == "double_chance_1x":
                    if gh >= ga:
                        self.legs_won[t_id].add(fid)
                        final_lines.append(f"• Ticket {t_id} ({m_label}): <b>✅ VINTO</b> (1X preso)")
                    else:
                        final_lines.append(f"• Ticket {t_id} ({m_label}): <b>❌ PERSO</b>")
                elif b_type == "double_chance_x2":
                    if ga >= gh:
                        self.legs_won[t_id].add(fid)
                        final_lines.append(f"• Ticket {t_id} ({m_label}): <b>✅ VINTO</b> (X2 preso)")
                    else:
                        final_lines.append(f"• Ticket {t_id} ({m_label}): <b>❌ PERSO</b>")
                elif b_type == "combo_x2_u35":
                    if ga >= gh and tot_goals <= 3:
                        self.legs_won[t_id].add(fid)
                        final_lines.append(f"• Ticket {t_id} ({m_label}): <b>✅ VINTO</b> (X2 + Under 3.5 preso)")
                    else:
                        final_lines.append(f"• Ticket {t_id} ({m_label}): <b>❌ PERSO</b>")
                elif b_type == "match_winner_1":
                    if gh > ga:
                        self.legs_won[t_id].add(fid)
                        final_lines.append(f"• Ticket {t_id} ({m_label}): <b>✅ VINTO</b> (1 preso)")
                    else:
                        final_lines.append(f"• Ticket {t_id} ({m_label}): <b>❌ PERSO</b>")
                elif b_type == "match_winner_2":
                    if ga > gh:
                        self.legs_won[t_id].add(fid)
                        final_lines.append(f"• Ticket {t_id} ({m_label}): <b>✅ VINTO</b> (2 preso)")
                    else:
                        final_lines.append(f"• Ticket {t_id} ({m_label}): <b>❌ PERSO</b>")

            msg = (
                f"🏁 <b>FISCHIO FINALE! RISULTATO DEFINITIVO</b>\n\n"
                f"{cfg['competition']}\n"
                f"🏆 <b>{home} {gh} - {ga} {away}</b> (FT)\n\n"
                f"📋 <b>Esito Ufficiale:</b>\n" + "\n".join(final_lines)
            )
            send_telegram(msg)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] FT notified: {home} {gh}-{ga} {away}", flush=True)

        # Aggiorna lo stato corrente
        st["status"] = new_status
        st["elapsed"] = elapsed

    def check_secondary_stats(self, in_play_ids: list[int]):
        """Verifica corner, cartellini e falli giocatori per i match in-play."""
        for fid in in_play_ids:
            cfg = FIXTURES_CONFIG.get(fid)
            if not cfg:
                continue

            has_corner = any("corner" in b["type"] for b in cfg["bets"])
            has_cards = any("card" in b["type"] for b in cfg["bets"])
            has_player_fouls = any("player" in b["type"] for b in cfg["bets"])

            if not (has_corner or has_cards or has_player_fouls):
                continue

            try:
                raw_stats = self.collector.fixture_stats(fid).get("response", [])
                st = self.match_states[fid]
                
                if raw_stats:
                    c_home = 0
                    c_away = 0
                    cards_tot = 0
                    for t_entry in raw_stats:
                        t_name = t_entry["team"]["name"]
                        s_dict = {s["type"]: s["value"] for s in t_entry.get("statistics", [])}
                        corn = s_dict.get("Corner Kicks") or 0
                        y_card = s_dict.get("Yellow Cards") or 0
                        r_card = s_dict.get("Red Cards") or 0
                        cards_tot += (y_card + (r_card * 2))
                        if st["home_name"] and t_name == st["home_name"]:
                            c_home = corn
                        else:
                            c_away = corn

                    # Check total corners (Midtjylland)
                    tot_corners = c_home + c_away
                    if tot_corners >= 9 and (fid, "over_corners_total") not in self.notified_milestones:
                        for b in cfg["bets"]:
                            if b["type"] == "over_corners_total":
                                self.notified_milestones.add((fid, "over_corners_total"))
                                self.legs_won[b["ticket"]].add(fid)
                                send_telegram(
                                    f"🚩 <b>OVER 8.5 CORNER RAGGIUNTO! ✅</b>\n\n"
                                    f"{st['home_name']} vs {st['away_name']}\n"
                                    f"Totale Corner: <b>{tot_corners}</b> ({c_home} - {c_away})\n"
                                    f"🎯 <b>Ticket {b['ticket']}</b>: Selezione VINTA al 100%!"
                                )

                    # Check home corners (Palermo)
                    if c_home >= 5 and (fid, "home_corners") not in self.notified_milestones:
                        for b in cfg["bets"]:
                            if b["type"] == "home_corners":
                                self.notified_milestones.add((fid, "home_corners"))
                                self.legs_won[b["ticket"]].add(fid)
                                send_telegram(
                                    f"🚩 <b>PALERMO OVER 4.5 CORNER RAGGIUNTO! ✅</b>\n\n"
                                    f"Palermo vs {st['away_name']}\n"
                                    f"Corner Palermo: <b>{c_home}</b>\n"
                                    f"🎯 <b>Ticket {b['ticket']}</b>: Selezione VINTA al 100%!"
                                )

                    # Check cards (Getafe)
                    if cards_tot >= 5 and (fid, "over_cards") not in self.notified_milestones:
                        for b in cfg["bets"]:
                            if b["type"] == "over_cards":
                                self.notified_milestones.add((fid, "over_cards"))
                                self.legs_won[b["ticket"]].add(fid)
                                send_telegram(
                                    f"🟨 <b>OVER 4.5 CARTELLINI RAGGIUNTO! ✅</b>\n\n"
                                    f"Getafe vs Celta Vigo\n"
                                    f"Totale Cartellini: <b>{cards_tot}</b>\n"
                                    f"🎯 <b>Ticket {b['ticket']}</b>: Selezione VINTA al 100%!"
                                )

            except Exception as e:
                print(f"[STATS ERROR fixture {fid}]: {e}", flush=True)

            # Check player fouls drawn (Zaccagni / Oyarzabal)
            if has_player_fouls:
                try:
                    p_res = self.collector._get("fixtures/players", {"fixture": fid}).get("response", [])
                    for team_data in p_res:
                        for p_entry in team_data.get("players", []):
                            p_name = p_entry.get("player", {}).get("name", "")
                            stats_list = p_entry.get("statistics", [])
                            if not stats_list:
                                continue
                            fouls_drawn = stats_list[0].get("fouls", {}).get("drawn") or 0

                            for b in cfg["bets"]:
                                if b["type"] == "player_fouls_drawn":
                                    target_str = b["player_name"].lower()
                                    if target_str in p_name.lower():
                                        milestone_key = (fid, f"foul_{target_str}")
                                        if fouls_drawn >= 2 and milestone_key not in self.notified_milestones:
                                            self.notified_milestones.add(milestone_key)
                                            self.legs_won[b["ticket"]].add(fid)
                                            send_telegram(
                                                f"🎯 <b>FALLI SUBITI RAGGIUNTI! ✅</b>\n\n"
                                                f"👤 <b>{p_name}</b> ha subito <b>{fouls_drawn} falli</b>!\n"
                                                f"🎯 <b>Ticket {b['ticket']}</b> ({b['market']}): Selezione VINTA al 100%!"
                                            )
                except Exception as e:
                    print(f"[PLAYER FOULS ERROR fixture {fid}]: {e}", flush=True)

    def run_loop(self):
        print("=" * 75, flush=True)
        print("🤖 [BAGENT] TELEGRAM LIVE SENTINEL SCOREBOARD ATTIVA (V2 OTTIMIZZATA)", flush=True)
        print("📡 Monitoraggio 9 match per 4 Schedine (#56, #57, #54, #55)", flush=True)
        print(f"⏱️ Frequenza scansione: 40 secondi in-play | Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print("=" * 75, flush=True)

        all_fids_str = "-".join(str(k) for k in FIXTURES_CONFIG.keys())
        poll_count = 0

        while True:
            poll_count += 1
            now_str = datetime.now().strftime("%H:%M:%S")
            try:
                raw = self.collector._get("fixtures", {"ids": all_fids_str})
                fixtures_list = raw.get("response", [])
                
                in_play_ids = []
                for fx in fixtures_list:
                    fid = fx["fixture"]["id"]
                    status = fx["fixture"]["status"]["short"]
                    if status in ("1H", "2H", "HT", "ET", "LIVE"):
                        in_play_ids.append(fid)
                    self.process_fixture_data(fx)

                # Check secondary stats (corner, cards, player fouls)
                if in_play_ids:
                    self.check_secondary_stats(in_play_ids)

                # Check if any full ticket is won
                self.check_full_tickets()

                print(f"[{now_str}] Poll #{poll_count} OK — In-play match attivi: {len(in_play_ids)}/{len(FIXTURES_CONFIG)}", flush=True)

            except Exception as e:
                print(f"[{now_str}] Errore durante il polling: {e}", flush=True)

            sleep_sec = 40 if in_play_ids else 60
            time.sleep(sleep_sec)

if __name__ == "__main__":
    bot = LiveTelegramScoreboard()
    bot.run_loop()
