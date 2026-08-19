class AnalysisEngine:

    def __init__(self):

        self._agents = []

    def register(self, agent):

        self._agents.append(agent)

    def analyze(self, context):

        evidences = []

        for agent in self._agents:

            evidence = agent.analyze(context)

            if evidence is not None:

                evidences.append(evidence)

        return evidences