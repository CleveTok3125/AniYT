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
