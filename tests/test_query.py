from ani_yt.query import Query


class TestQuery:
    def test_search_basic(self):
        q = Query()
        data = [("One Piece EP 1", "https://youtube.com/1"), ("Naruto EP 1", "https://youtube.com/2")]
        result = q.search(data, "piece")
        assert len(result) == 1
        assert "One Piece" in result[0][0]

    def test_search_case_sensitive(self):
        q = Query(case_sensitive=True)
        data = [("One Piece", "https://youtube.com/1"), ("one piece", "https://youtube.com/2")]
        result = q.search(data, "One")
        assert len(result) == 1
        assert result[0][0] == "One Piece"

    def test_search_no_match(self):
        q = Query()
        data = [("One Piece", "https://youtube.com/1")]
        result = q.search(data, "Bleach")
        assert result == []

    def test_fuzzysearch_basic(self):
        q = Query()
        data = [("One Piece", "https://youtube.com/1"), ("Naruto", "https://youtube.com/2")]
        result = q.fuzzysearch(data, "One", score=0)
        assert len(result) >= 1

    def test_fuzzysearch_case_sensitive(self):
        q = Query(case_sensitive=True)
        data = [("One Piece", "https://youtube.com/1"), ("xyz", "https://youtube.com/2")]
        result = q.fuzzysearch(data, "One", score=0)
        assert len(result) == 1
        assert result[0][0] == "One Piece"
        assert result[0][0] == "One Piece"

    def test_fuzzysearch_no_match_low_score(self):
        q = Query()
        data = [("One Piece", "https://youtube.com/1")]
        result = q.fuzzysearch(data, "xyzabc", score=100)
        assert result == []
