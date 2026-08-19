from providers.tennis.atp.parser import ATPParser
from providers.tennis.atp.normalizer import ATPNormalizer

from engines.evidence.statistics_engine import StatisticsEngine
from engines.evidence.fusion_engine import FusionEngine


parser = ATPParser()
normalizer = ATPNormalizer()

statistics = StatisticsEngine()
fusion = FusionEngine()

tournaments = parser.parse()

competition = normalizer.competition(tournaments[0])

raw_match = tournaments[0].matches[0]

match = normalizer.match(raw_match, competition)

evidences = statistics.analyze(match)

prediction = fusion.predict(match, evidences)

print()

print("=" * 70)

print(match.home.name)

print("vs")

print(match.away.name)

print()

print("Prediction")

print(prediction)

print()

print("Evidence")

for evidence in evidences:

    print(evidence)