import re


class NameNormalizer:

    @staticmethod
    def normalize(name: str) -> str:
        """
        Normalizza il nome di un giocatore.
        Esempi:
        - Zverev, Alexander -> alexander zverev
        - Alexander   Zverev -> alexander zverev
        - A. Zverev -> a zverev
        """

        name = name.lower().strip()

        # virgole -> spazio
        name = name.replace(",", " ")

        # punti
        name = name.replace(".", "")

        # spazi multipli
        name = re.sub(r"\s+", " ", name)

        parts = name.split()

        if len(parts) == 2:

            first, second = parts

            # cognome prima del nome
            if len(first) > len(second):
                parts = [second, first]

        return " ".join(parts)