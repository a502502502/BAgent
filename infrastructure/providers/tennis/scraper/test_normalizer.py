from utils.normalizer import NameNormalizer


names = [

    "Alexander Zverev",
    "Zverev Alexander",
    "Zverev, Alexander",
    "A. Zverev",
    "Alexander   Zverev"

]

for n in names:
    print(NameNormalizer.normalize(n))