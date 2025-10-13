from typing import List

from .common import Video


class DataProcessing:
    @staticmethod
    def omit(data: dict, status: str = "") -> List[Video]:
        videos: List[Video] = []

        for entry in data.get("entries", []):
            if entry.get("_type") == "url":
                video_item = {
                    "video_title": entry["title"],
                    "video_url": entry["url"],
                    "status": status,
                }

                videos.append(video_item)

        return videos

    @staticmethod
    def split_list(lst: list, n: int) -> list:
        return [lst[i : i + n] for i in range(0, len(lst), n)]

    @staticmethod
    def sort(lst: list, key=lambda x: x[0], reverse: bool = False) -> list:
        return sorted(lst, key=key, reverse=reverse)

    @staticmethod
    def merge_list(
        old_videos: List[Video], new_videos: List[Video], truncate: bool = True
    ) -> List[Video]:
        new_urls = {v["video_url"] for v in new_videos}

        if truncate:
            old_videos = [v for v in old_videos if v["video_url"] in new_urls]

        existing = {v["video_url"]: v for v in old_videos}

        for v in new_videos:
            url = v["video_url"]
            if url in existing:
                # Update video_title, keep status
                existing[url]["video_title"] = v["video_title"]
            else:
                old_videos.append(v)

        return DataProcessing.sort(old_videos, key=lambda x: x["video_title"])

    @staticmethod
    def merge_list_preserve_order(old_list: list, new_list: list) -> list:
        existing_urls = {item[1] for item in old_list}
        for item in new_list:
            if item[1] not in existing_urls:
                old_list.append(item)
                existing_urls.add(item[1])
        return old_list

    @staticmethod
    def merge_args(default_args: list, extra_args: list) -> list:
        merged = []
        seen = set()

        for arg in extra_args:
            if arg not in seen:
                merged.append(arg)
                seen.add(arg)

        for arg in default_args:
            if arg not in seen:
                merged.append(arg)
                seen.add(arg)

        return merged

    @staticmethod
    def dedup_args(args: list) -> list:
        seen = set()
        result = []
        for arg in args:
            if arg not in seen:
                result.append(arg)
                seen.add(arg)
        return result

    def dedup_args_keep_last(args: list) -> list:
        seen = set()
        result = []
        for arg in reversed(args):
            if arg not in seen:
                result.append(arg)
                seen.add(arg)
        return list(reversed(result))
