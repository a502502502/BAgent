# Script to build the master combined ticket for tonight's 7 Nations League matches

legs = [
    {
        "match": "Italia vs Turchia",
        "market": "1X + Multigol 1-4",
        "odd": 1.33,
        "prob": 0.775,
        "reasoning": "Italia nettamente favorita che controlla il match; il Multigol 1-4 esclude sia lo 0-0 che goleade improbabili a 5+ reti."
    },
    {
        "match": "Francia vs Belgio",
        "market": "1X + Over 1.5",
        "odd": 1.35,
        "prob": 0.750,
        "reasoning": "Francia superiore ma Belgio pericoloso in ripartenza; combinazione perfetta per 2-0, 1-1, 2-1, 3-1."
    },
    {
        "match": "Bosnia Erzegovina vs Polonia",
        "market": "Multigol 1-3",
        "odd": 1.36,
        "prob": 0.720,
        "reasoning": "Gara ad altissima intensita fisica a Zenica; poche occasioni pulite, copertura totale per 1-0, 0-1, 1-1, 2-0, 0-2, 2-1."
    },
    {
        "match": "Ucraina vs Ungheria",
        "market": "Under 3.5",
        "odd": 1.25,
        "prob": 0.820,
        "reasoning": "Scontro diretto tattico e bloccato in campo neutro; entrambe partono prudenti, baricentro compatto."
    },
    {
        "match": "Irlanda del Nord vs Georgia",
        "market": "1X o Under 2.5 (Chance Mix) / Under 3.5",
        "market_label": "Under 3.5",
        "odd": 1.22,
        "prob": 0.829,
        "reasoning": "Belfast concede poco spettacolo; ritmi spezzati da duelli aerei e difese schierate."
    },
    {
        "match": "Romania vs Svezia",
        "market": "X2 + Multigol 1-5",
        "odd": 1.32,
        "prob": 0.765,
        "reasoning": "Svezia tecnicamente superiore con Isak e Gyokeres, paracadute totale fino a 5 gol sul pareggio o vittoria ospite."
    },
    {
        "match": "Montenegro vs Armenia",
        "market": "1X + Under 3.5",
        "odd": 1.45,
        "prob": 0.730,
        "reasoning": "Montenegro fortissimo tra le mura amiche contro un'Armenia poco prolifica lontano da casa."
    }
]

total_odd = 1.0
total_prob = 1.0
for leg in legs:
    total_odd *= leg["odd"]
    total_prob *= leg["prob"]

print(f"Schedina Completa Nations League (7 Eventi):")
print(f"Quota Complessiva: {total_odd:.2f}")
print(f"Probabilita Congiunta Stimata: {total_prob*100:.2f}%")
print(f"Potenziale Vincita con 10 Euro: {total_odd * 10:.2f} Euro")
