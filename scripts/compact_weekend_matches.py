import json

data = json.load(open('data/netwin_live_odds.json', encoding='utf-8'))
m_list = [m for m in data.get('matches', []) if any(m.get('kickoff', '').startswith(d) for d in ['20261003', '20261004'])]

print(f"Total weekend matches (3-4 Oct): {len(m_list)}\n")
for idx, m in enumerate(sorted(m_list, key=lambda x: x.get('kickoff', '')), 1):
    ko = m.get('kickoff', '')
    dt_str = f"{ko[6:8]}/{ko[4:6]}/{ko[0:4]} {ko[9:14]}"
    name = m.get('match_name')
    tour = m.get('tournament')
    mkts = m.get('markets', {})
    
    _1x2 = mkts.get('1X2', {})
    dc = mkts.get('DOPPIA_CHANCE', {})
    uo25 = mkts.get('UNDER_OVER', {}).get('2.5', {})
    uo15 = mkts.get('UNDER_OVER', {}).get('1.5', {})
    gg = mkts.get('GOL_NOGOL', {})
    pt = mkts.get('PRIMO_TEMPO', {})
    cm = mkts.get('CHANCE_MIX', {})
    
    print(f"[{idx}] {dt_str} | {tour} | {name}")
    print(f"    1X2: 1@{_1x2.get('1')} X@{_1x2.get('X')} 2@{_1x2.get('2')} | 1X@{dc.get('1X')} X2@{dc.get('X2')}")
    print(f"    U/O 2.5: U@{uo25.get('Under')} O@{uo25.get('Over')} | U/O 1.5: U@{uo15.get('Under')} O@{uo15.get('Over')}")
    print(f"    Gol: @{gg.get('Gol')} | NoGol: @{gg.get('NoGol')}")
    print(f"    MG 0-1 1°T: @{pt.get('MultiGol 0-1 1° Tempo')} | U 1.5 1°T: @{pt.get('Under 1.5 1° Tempo')}")
    # Top 2 Chance Mix
    cm_samples = [(k, v) for k, v in cm.items() if 1.30 <= v <= 1.70][:3]
    if cm_samples:
        print(f"    Chance Mix: {cm_samples}")
    print("-" * 65)
