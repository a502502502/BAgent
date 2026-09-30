import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/bagent.db')
cursor = conn.cursor()

oct1_matches = [
    ("Germany", "Serbia", "Germania vs Serbia"),
    ("Greece", "Netherlands", "Grecia vs Olanda"),
    ("Denmark", "Portugal", "Danimarca vs Portogallo"),
    ("Wales", "Norway", "Galles vs Norvegia"),
    ("Azerbaijan", "Liechtenstein", "Azerbaigian vs Liechtenstein"),
    ("Malta", "Gibraltar", "Malta vs Gibilterra"),
    ("Republic of Ireland", "Austria", "Irlanda vs Austria"),
    ("Israel", "Kosovo", "Israele vs Kosovo"),
]

def get_team_stats(team_name):
    # Cerca tutte le partite FT di questa squadra in Nations League
    q = """
        SELECT 
            home_team, away_team,
            home_corners, away_corners,
            home_yellow_cards, away_yellow_cards,
            home_red_cards, away_red_cards,
            home_shots, away_shots
        FROM matches
        WHERE league LIKE '%Nations League%' AND status='FT'
          AND (home_team = ? OR away_team = ?)
    """
    cursor.execute(q, (team_name, team_name))
    rows = cursor.fetchall()
    
    cf_list = []
    ca_list = []
    yc_list = []
    yca_list = []
    shots_list = []
    
    for r in rows:
        is_home = (r[0] == team_name)
        corners_for = r[2] if is_home else r[3]
        corners_against = r[3] if is_home else r[2]
        yc_for = r[4] if is_home else r[5]
        yc_against = r[5] if is_home else r[4]
        shots_for = r[8] if is_home else r[9]
        
        if corners_for is not None: cf_list.append(corners_for)
        if corners_against is not None: ca_list.append(corners_against)
        if yc_for is not None: yc_list.append(yc_for)
        if yc_against is not None: yca_list.append(yc_against)
        if shots_for is not None: shots_list.append(shots_for)
        
    n = len(rows)
    return {
        "played": n,
        "avg_cf": sum(cf_list)/n if n else 4.0,
        "avg_ca": sum(ca_list)/n if n else 4.0,
        "avg_yc": sum(yc_list)/n if n else 2.0,
        "avg_yca": sum(yca_list)/n if n else 2.0,
        "avg_shots": sum(shots_list)/n if n else 12.0,
        "history": [(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows]
    }

print("=========================================================================================")
print("📊 REPORT ANALITICO CORNER & CARTELLINI — UEFA NATIONS LEAGUE (01/10/2026)")
print("=========================================================================================\n")

for h_team, a_team, label in oct1_matches:
    hs = get_team_stats(h_team)
    as_ = get_team_stats(a_team)
    
    # Stima angoli: media incrociata
    exp_h_corners = (hs["avg_cf"] + as_["avg_ca"]) / 2.0
    exp_a_corners = (as_["avg_cf"] + hs["avg_ca"]) / 2.0
    exp_total_corners = exp_h_corners + exp_a_corners
    
    # Stima cartellini:
    exp_h_yc = (hs["avg_yc"] + as_["avg_yca"]) / 2.0
    exp_a_yc = (as_["avg_yc"] + hs["avg_yca"]) / 2.0
    exp_total_cards = exp_h_yc + exp_a_yc
    
    print(f"⚽ {label}")
    print(f"   🚩 CORNER: Attesi Totali ~ {exp_total_corners:.2f} ({exp_h_corners:.2f} Casa - {exp_a_corners:.2f} Ospite)")
    print(f"      • {h_team}: CF {hs['avg_cf']:.1f}, CA {hs['avg_ca']:.1f} (Tiri medi: {hs['avg_shots']:.1f})")
    print(f"      • {a_team}: CF {as_['avg_cf']:.1f}, CA {as_['avg_ca']:.1f} (Tiri medi: {as_['avg_shots']:.1f})")
    print(f"   🟨 CARTELLINI: Attesi Totali ~ {exp_total_cards:.2f} ({exp_h_yc:.2f} Casa - {exp_a_yc:.2f} Ospite)")
    print(f"      • {h_team}: Gialli fatti {hs['avg_yc']:.1f}, subiti {hs['avg_yca']:.1f}")
    print(f"      • {a_team}: Gialli fatti {as_['avg_yc']:.1f}, subiti {as_['avg_yca']:.1f}")
    print(f"   Storico {h_team}: {hs['history']}")
    print(f"   Storico {a_team}: {as_['history']}\n")
