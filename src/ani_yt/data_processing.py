class DataProcessing:
    @staticmethod
    def omit(data):
        return [
            (entry["title"], entry["url"])
            for entry in data.get("entries", [])
            if entry.get("_type") == "url"
        ]

    @staticmethod
    def split_list(lst, n):
        return [lst[i : i + n] for i in range(0, len(lst), n)]

    @staticmethod
    def sort(lst, key=lambda x: x[0], reverse=False):
        return sorted(lst, key=key, reverse=reverse)

    @staticmethod
    def merge_list(old_list, new_list, truncate=True):
        mapping = {v: k for k, v in new_list}

        if truncate:
            old_list = [
                sublist for sublist in old_list if sublist[1] in set(mapping.keys())
            ]

        for old_list_item in old_list:
            if old_list_item[1] in mapping:
                old_list_item[0] = mapping[old_list_item[1]]

        existing_values = {sublist[1] for sublist in old_list}

        old_list.extend([k, v] for k, v in new_list if v not in existing_values)

        return DataProcessing.sort(old_list)

    @staticmethod
    def merge_list_preserve_order(old_list, new_list):
        existing_urls = {item[1] for item in old_list}
        for item in new_list:
            if item[1] not in existing_urls:
                old_list.append(item)
                existing_urls.add(item[1])
        return old_list

    @staticmethod
    def merge_args(default_args, extra_args):
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
    def dedup_args(args):
        seen = set()
        result = []
        for arg in args:
            if arg not in seen:
                result.append(arg)
                seen.add(arg)
        return result

    def dedup_args_keep_last(args):
        seen = set()
        result = []
        for arg in reversed(args):
            if arg not in seen:
                result.append(arg)
                seen.add(arg)
        return list(reversed(result))
