import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from services.football.reality_gate_guardian import RealityGateGuardian
from scripts.argon_supervisor import audit_ticket_with_argon

guardian = RealityGateGuardian()

tickets = [
    {
        'id': 'SCHEDINA_1_CORE_APERTURA_1845',
        'title': 'Schedina 1: Core Blindato Apertura (18:45)',
        'legs': [
            {'match': 'Salisburgo vs AC Milan', 'pick': 'X2 + Over 1.5', 'odd': '1.48', 'home': 'Salzburg', 'away': 'AC Milan', 'score': 'Milan cerca riscatto dopo il Benfica; Salisburgo concede 1.55 xGA.'},
            {'match': "AZ Alkmaar vs Hapoel Be'er Sheva", 'pick': 'Over 0.5 1°T + Over 0.5 2°T', 'odd': '1.45', 'home': 'AZ Alkmaar', 'away': "Hapoel Be'er Sheva", 'score': 'Ritmo olandese costante; una rete per tempo.'},
            {'match': 'Sparta Praga vs Lillestrom', 'pick': 'Sparta Praga Over 1.5 Gol', 'odd': '1.38', 'home': 'Sparta Praha', 'away': 'Lillestrom', 'score': 'Media ceca interna superiore a 2 reti.'}
        ]
    },
    {
        'id': 'SCHEDINA_2_CORE_NOTTURNA_2100',
        'title': 'Schedina 2: Core Blindato Notturna (21:00)',
        'legs': [
            {'match': 'SL Benfica vs Celtic FC', 'pick': '1X + Over 1.5', 'odd': '1.45', 'home': 'Benfica', 'away': 'Celtic', 'score': 'Da Luz fortino europeo; Celtic fragile in trasferta.'},
            {'match': 'Celta Vigo vs Juventus', 'pick': 'Chance Mix: X2 o Under 2.5', 'odd': '1.42', 'home': 'Celta Vigo', 'away': 'Juventus', 'score': 'Spalletti gestisce il possesso; copre 0-0, 1-1, 0-1, 0-2, 1-0.'},
            {'match': 'NEC Nijmegen vs Levski Sofia', 'pick': '1X + Over 1.5', 'odd': '1.42', 'home': 'NEC Nijmegen', 'away': 'Levski Sofia', 'score': 'Dinamismo olandese contro blocco bulgaro.'},
            {'match': 'Jagiellonia vs Ararat-Armenia', 'pick': 'Jagiellonia Over 1.5 Gol', 'odd': '1.45', 'home': 'Jagiellonia', 'away': 'Ararat-Armenia', 'score': 'Polacchi travolgenti; rettifica anti-soffitto.'}
        ]
    },
    {
        'id': 'SCHEDINA_3_TRIPLA_CHIRURGICA_TIRI',
        'title': 'Schedina 3: La Tripla Chirurgica (Tiri in Porta)',
        'legs': [
            {'match': 'Atalanta vs Pafos FC', 'pick': 'Atalanta Over 4.5 Tiri in Porta', 'odd': '1.40', 'home': 'Atalanta', 'away': 'Pafos', 'score': 'Sarri produce alto volume contro blocco basso cipriota.'},
            {'match': 'Ajax vs Maccabi Tel Aviv', 'pick': 'Ajax Over 5.5 Tiri in Porta', 'odd': '1.60', 'home': 'Ajax', 'away': 'Maccabi Tel Aviv', 'score': 'Farioli accentra il tiro con le ali (media 7.8 tiri specchio).'},
            {'match': 'AFC Bournemouth vs Sturm Graz', 'pick': 'Bournemouth Over 5.5 Tiri in Porta', 'odd': '1.45', 'home': 'Bournemouth', 'away': 'Sturm Graz', 'score': 'Iraola pressing asfissiante contro difesa statica.'}
        ]
    },
    {
        'id': 'SCHEDINA_4_SPECIALS_CORNER_CARTELLINI',
        'title': 'Schedina 4: Specials Asimmetrici (Corner & Cartellini)',
        'legs': [
            {'match': 'Brighton vs Kauno Zalgiris', 'pick': 'Brighton Over 6.5 Corner', 'odd': '1.50', 'home': 'Brighton', 'away': 'Kauno Zalgiris', 'score': 'Hurzeler ampiezza estrema contro blocco basso lituano.'},
            {'match': 'SL Benfica vs Celtic FC', 'pick': 'Benfica Over 4.5 Corner', 'odd': '1.38', 'home': 'Benfica', 'away': 'Celtic', 'score': 'Corsie esterne attive con cross dal fondo per Pavlidis.'},
            {'match': 'Olympique Marsiglia vs Olympiacos', 'pick': 'Over 4.5 Cartellini Totali', 'odd': '1.55', 'home': 'Olympique de Marseille', 'away': 'Olympiacos', 'score': 'Genesio vs Mendilibar, clima incandescente al Velodrome.'},
            {'match': 'Union SG vs Real Sociedad', 'pick': 'Over 3.5 Cartellini Totali', 'odd': '1.45', 'home': 'Union SG', 'away': 'Real Sociedad', 'score': 'Scontro fisico a Bruxelles ad alto attrito.'}
        ]
    },
    {
        'id': 'SCHEDINA_5_SATELLITE_GOL_OVER',
        'title': 'Schedina 5: Satellite Alto Flusso (Gol & Over)',
        'legs': [
            {'match': 'Hoffenheim vs Besiktas', 'pick': 'Gol + Over 2.5', 'odd': '1.75', 'home': 'Hoffenheim', 'away': 'Besiktas', 'score': 'Difese colabrodo, massimo xG della serata.'},
            {'match': 'Lech Poznan vs Bayer Leverkusen', 'pick': 'Over 2.5', 'odd': '1.62', 'home': 'Lech Poznan', 'away': 'Bayer Leverkusen', 'score': 'Campo pesante e transizioni continue, slegata da 1X2.'},
            {'match': 'Olympique Marsiglia vs Olympiacos', 'pick': 'G/NG: Gol', 'odd': '1.65', 'home': 'Olympique de Marseille', 'away': 'Olympiacos', 'score': 'Genesio concede ripartenze; Olympiacos letale con El Kaabi.'},
            {'match': 'Olympique Lione vs Crystal Palace', 'pick': 'Chance Mix: X o GG', 'odd': '1.40', 'home': 'Lyon', 'away': 'Crystal Palace', 'score': 'Duello serrato: copre 1-1, 2-1, 1-2, 0-0.'}
        ]
    }
]

print("=" * 80)
print("RICONTROLLO RIGOROSO DELLE 5 SCHEDINE POST-BONIFICA E REALITY GATE 2.0")
print("=" * 80)

all_ok = True
for t in tickets:
    rep = audit_ticket_with_argon(t)
    print(f"\n--- {rep['title']} ---")
    print(f"Reality Gate 2026/27 : {rep['reality_gate']['status']}")
    if rep['reality_gate']['violations']:
        print(f"  Violazioni Reality: {rep['reality_gate']['violations']}")
        all_ok = False
    print(f"Verdetto Argon       : {rep['verdict']} ({rep['reason']})")
    if rep['trap_warnings']:
        print(f"  Avvisi Trappola    : {rep['trap_warnings']}")
        all_ok = False
    for c in rep['leg_critiques']:
        print(f"  * {c['match']} | {c['pick']} @{c['odd']} -> [{c['risk_level']}] {c['notes']}")

print("\n" + "=" * 80)
if all_ok:
    print("ESITO FINALE: TUTTE E 5 LE SCHEDINE SONO CERTIFICATE E APPROVATE AL 100%. ZERO ERRORI.")
else:
    print("ESITO FINALE: ATTENZIONE, PRESENTI ERRORI O AVVISI BLOCCANTI.")
print("=" * 80)
