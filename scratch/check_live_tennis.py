
raise SystemExit(
    "TENNIS BAN (22/09/2026): script disabilitato. BAgent opera solo sul calcio."
)
import requests, re

url = 'https://local-it.flashscore.ninja/2/x/feed/f_2_0_1_it_1'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0', 'x-fsign': 'SW9D1eZo'})
for b in r.text.split('~AA÷'):
    if any(k in b.lower() for k in ['rus', 'ristic', 'hercog', 'romero']):
        m_h = re.search(r'AE÷([^¬]+)', b)
        m_a = re.search(r'AF÷([^¬]+)', b)
        m_st = re.search(r'AB÷([^¬]+)', b)
        m_sh = re.search(r'AG÷([^¬]+)', b)
        m_sa = re.search(r'AH÷([^¬]+)', b)
        ba = re.search(r'BA÷([^¬]+)', b)
        bb = re.search(r'BB÷([^¬]+)', b)
        bc = re.search(r'BC÷([^¬]+)', b)
        bd = re.search(r'BD÷([^¬]+)', b)
        h = m_h.group(1) if m_h else '?'
        a = m_a.group(1) if m_a else '?'
        st = m_st.group(1) if m_st else '?'
        sh = m_sh.group(1) if m_sh else '0'
        sa = m_sa.group(1) if m_sa else '0'
        s1 = f'{ba.group(1)}-{bb.group(1)}' if ba and bb else ''
        s2 = f'{bc.group(1)}-{bd.group(1)}' if bc and bd else ''
        print(f'{h} vs {a} | Sets: {sh}-{sa} ({s1} {s2}) | Status: {st}')
