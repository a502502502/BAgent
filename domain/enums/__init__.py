from enum import Enum


class KnowledgeKey(str, Enum):

    LEAGUE_POSITION = "LEAGUE_POSITION"

    ELO = "ELO"

    COUNTRY = "COUNTRY"

    AGE = "AGE"

    HEIGHT = "HEIGHT"

    WEIGHT = "WEIGHT"

    LAST_10_FORM = "LAST_10_FORM"

    REST_DAYS = "REST_DAYS"

    XG = "XG"
