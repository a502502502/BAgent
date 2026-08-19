from enum import Enum


class KnowledgeKey(str, Enum):

    ATP_RANK = "ATP_RANK"

    ELO = "ELO"

    COUNTRY = "COUNTRY"

    AGE = "AGE"

    HAND = "HAND"

    HEIGHT = "HEIGHT"

    WEIGHT = "WEIGHT"

    SURFACE_WINRATE = "SURFACE_WINRATE"

    LAST_10_FORM = "LAST_10_FORM"

    REST_DAYS = "REST_DAYS"