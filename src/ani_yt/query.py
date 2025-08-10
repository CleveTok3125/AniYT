from rapidfuzz import process

# Custom lib
from .data_processing import DataProcessing
from . import _query


class Query:
    def __init__(self, CASE=False):
        self.case = CASE

    @staticmethod
    def calculate_match_score(title, query):
        """
        score = 0
        score += sum(1 for word in query if word in title)
        return score
        """
        raise DeprecationWarning(
            f"{Query.calculate_match_score.__name__} is deprecated, please use {_query.calculate_match_score.__name__} instead."
        )

    def search(self, data, query):
        if not self.case:
            query = query.lower()
        query = set(query.split())
        result = []
        for title, url in data:
            title_to_check = title if self.case else title.lower()
            score = _query.calculate_match_score(title_to_check, query, min_length=3)
            if score > 0:
                result.append((title, url, score))
        result = DataProcessing.sort(result, key=lambda x: x[2], reverse=True)
        return [(title, url) for title, url, _ in result]

    def fuzzysearch(self, data, query, score=50):
        if not self.case:
            query = query.lower()
        result = process.extract(
            query,
            [item[0] if self.case else item[0].lower() for item in data],
            limit=None,
        )

        results_with_data = []
        for match in result:
            matched_name = match[0]
            matched_score = match[1]

            matched_item = next(
                (
                    item
                    for item in data
                    if (item[0] if self.case else item[0].lower()) == matched_name
                    and matched_score > score
                ),
                None,
            )

            if matched_item:
                results_with_data.append(
                    (matched_item[0], matched_item[1], matched_score)
                )
        results_with_data = DataProcessing.sort(
            results_with_data, key=lambda x: x[2], reverse=True
        )
        return [(title, url) for title, url, _ in results_with_data]
