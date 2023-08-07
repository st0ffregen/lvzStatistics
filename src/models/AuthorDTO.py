from src.models.MatchingType import MatchingType


class AuthorDTO:
    def __init__(self, name: str | None, abbreviation: str | None, matching_certainty: float | None, matching_type: MatchingType, article_id: int | None = None):
        self.name = name
        self.abbreviation = abbreviation
        self.matching_certainty = matching_certainty
        self.matching_type = matching_type
        self.article_id = article_id

    def __eq__(self, other):
        if not isinstance(other, AuthorDTO):
            raise NotImplementedError("other is not an AuthorRow")

        return self.name == other.name and self.abbreviation == other.abbreviation and self.matching_certainty == other.matching_certainty and self.matching_type == other.matching_type and self.article_id == other.article_id
