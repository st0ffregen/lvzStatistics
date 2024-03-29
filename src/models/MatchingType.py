from enum import StrEnum


class MatchingType(StrEnum):
    DIRECT_MATCH = "DIRECT_MATCH"
    FUZZY_MATCH = "FUZZY_MATCH"
    NO_MATCH = "NO_MATCH"
    ORGANIZATION_MATCH = "ORGANIZATION_MATCH"
    IS_FULL_NAME = "IS_FULL_NAME"
    IS_ABBREVIATION = "IS_ABBREVIATION"
