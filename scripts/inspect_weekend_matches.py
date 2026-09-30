import json

data = json.load(open('data/netwin_live_odds.json', encoding='utf-8'))
m_list = [m for m in data.get('matches', []) if any(m.get('kickoff', '').startswith(d) for d in ['20261003', '20261004'])]

print(f"Total weekend matches (3-4 Oct): {len(m_list)}")
for m in sorted(m_list, key=lambda x: x.get('kickoff', '')):
    print("=" * 60)
    print(f"{m.get('kickoff')} | {m.get('tournament')} | {m.get('match_name')}")
    mkts = m.get('markets', {})
    if '1X2' in mkts:
        print("  1X2:", mkts['1X2'])
    if 'DOPPIA_CHANCE' in mkts:
        print("  DC:", mkts['DOPPIA_CHANCE'])
    if 'UNDER_OVER' in mkts:
        uo = mkts['UNDER_OVER']
        print(f"  U/O 1.5: {uo.get('1.5')} | 2.5: {uo.get('2.5')} | 3.5: {uo.get('3.5')}")
    if 'GOL_NOGOL' in mkts:
        print("  GG/NG:", mkts['GOL_NOGOL'])
    if 'CHANCE_MIX' in mkts:
        print("  CHANCE_MIX:", mkts['CHANCE_MIX'])
    if 'MULTIGOL' in mkts:
        print("  MULTIGOL:", mkts['MULTIGOL'])
    if 'COMBO' in mkts:
        print("  COMBO sample:", list(mkts['COMBO'].items())[:6])
    if 'PRIMO_TEMPO' in mkts:
        print("  1°T:", mkts['PRIMO_TEMPO'])
