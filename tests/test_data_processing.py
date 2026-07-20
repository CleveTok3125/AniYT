from ani_yt.data_processing import DataProcessing

dp = DataProcessing


class TestOmit:
    def test_empty_entries(self):
        result = dp.omit({"entries": []})
        assert result == []

    def test_omit_url_type(self):
        data = {"entries": [{"_type": "url", "title": "V1", "url": "https://youtube.com/1"}]}
        result = dp.omit(data)
        assert len(result) == 1
        assert result[0]["video_title"] == "V1"
        assert result[0]["video_url"] == "https://youtube.com/1"
        assert result[0]["status"] == ""

    def test_omit_with_status(self):
        data = {"entries": [{"_type": "url", "title": "V1", "url": "https://youtube.com/1"}]}
        result = dp.omit(data, status="viewed")
        assert result[0]["status"] == "viewed"

    def test_omit_skips_non_url(self):
        data = {
            "entries": [
                {"_type": "url", "title": "V1", "url": "https://youtube.com/1"},
                {"_type": "playlist", "title": "P1", "url": "https://youtube.com/p1"},
            ]
        }
        result = dp.omit(data)
        assert len(result) == 1


class TestSplitList:
    def test_split_even(self):
        assert dp.split_list([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]

    def test_split_with_remainder(self):
        assert dp.split_list([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]

    def test_split_empty(self):
        assert dp.split_list([], 3) == []


class TestSort:
    def test_sort_default(self):
        assert dp.sort([(2, "b"), (1, "a")]) == [(1, "a"), (2, "b")]

    def test_sort_reverse(self):
        assert dp.sort([(1, "a"), (2, "b")], reverse=True) == [(2, "b"), (1, "a")]

    def test_sort_custom_key(self):
        data = [("z", 3), ("a", 1), ("m", 2)]
        result = dp.sort(data, key=lambda x: x[1])
        assert [x[1] for x in result] == [1, 2, 3]


class TestMergeList:
    def test_merge_new(self):
        old = [{"video_title": "A", "video_url": "https://youtube.com/a", "status": ""}]
        new = [{"video_title": "B", "video_url": "https://youtube.com/b", "status": ""}]
        result = dp.merge_list(old, new, truncate=False)
        assert len(result) == 2

    def test_merge_update_existing(self):
        old = [{"video_title": "A old", "video_url": "https://youtube.com/a", "status": "viewed"}]
        new = [{"video_title": "A new", "video_url": "https://youtube.com/a", "status": ""}]
        result = dp.merge_list(old, new, truncate=False)
        assert len(result) == 1
        assert result[0]["video_title"] == "A new"
        assert result[0]["status"] == "viewed"

    def test_merge_truncate(self):
        old = [
            {"video_title": "A", "video_url": "https://youtube.com/a", "status": ""},
            {"video_title": "B", "video_url": "https://youtube.com/b", "status": ""},
        ]
        new = [{"video_title": "A", "video_url": "https://youtube.com/a", "status": ""}]
        result = dp.merge_list(old, new, truncate=True)
        assert len(result) == 1


class TestMergeListPreserveOrder:
    def test_preserve_order(self):
        old = [("A", "https://youtube.com/a")]
        new = [("B", "https://youtube.com/b"), ("C", "https://youtube.com/c")]
        result = dp.merge_list_preserve_order(old, new)
        assert len(result) == 3
        assert result[0] == ("A", "https://youtube.com/a")

    def test_no_duplicates(self):
        old = [("A", "https://youtube.com/a")]
        new = [("A", "https://youtube.com/a"), ("B", "https://youtube.com/b")]
        result = dp.merge_list_preserve_order(old, new)
        assert len(result) == 2


class TestMergeArgs:
    def test_merge_extra_first(self):
        result = dp.merge_args(["--a", "--b"], ["--c", "--a"])
        assert result == ["--c", "--a", "--b"]

    def test_no_duplicates(self):
        result = dp.merge_args(["--a", "--b"], ["--b", "--c"])
        assert result == ["--b", "--c", "--a"]

    def test_empty_extra(self):
        result = dp.merge_args(["--a", "--b"], [])
        assert result == ["--a", "--b"]

    def test_empty_default(self):
        result = dp.merge_args([], ["--c"])
        assert result == ["--c"]


class TestDedupArgs:
    def test_dedup_basic(self):
        assert dp.dedup_args([1, 2, 2, 3, 1]) == [1, 2, 3]

    def test_dedup_empty(self):
        assert dp.dedup_args([]) == []


class TestDedupArgsKeepLast:
    def test_keep_last(self):
        assert dp.dedup_args_keep_last([1, 2, 3, 2, 1]) == [3, 2, 1]

    def test_keep_last_no_dupes(self):
        assert dp.dedup_args_keep_last([1, 2, 3]) == [1, 2, 3]

    def test_keep_last_empty(self):
        assert dp.dedup_args_keep_last([]) == []
