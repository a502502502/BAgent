class FactorRegistry:

    def __init__(self):

        self._factors = []

    def register(self, factor):

        self._factors.append(factor)

    def all(self):

        return self._factors