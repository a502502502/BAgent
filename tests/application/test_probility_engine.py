from application.reasoning.probability_engine import ProbabilityEngine
from domain.models.contribution import Contribution


engine = ProbabilityEngine()

probability = engine.calculate([

    Contribution(

        factor="Ranking",

        value=0.20,

        confidence=1.0,

        explanation="Ranking"

    ),

    Contribution(

        factor="Surface",

        value=0.10,

        confidence=1.0,

        explanation="Surface"

    )

])

print()

print("==========================")

print("HOME :", probability.home)

print("AWAY :", probability.away)

print("==========================")