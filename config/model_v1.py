from application.factors.factor_registry import FactorRegistry

from application.factors.ranking_factor import RankingFactor


registry = FactorRegistry()

registry.register(

    RankingFactor()

)