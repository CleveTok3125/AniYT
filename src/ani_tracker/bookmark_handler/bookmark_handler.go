package bookmark_handler

import (
	"encoding/json"
	"os"
)

type Bookmark map[string]string

func LoadBookmarkFromFile(filename string) (Bookmark, error) {
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}

	var bm Bookmark
	if err := json.Unmarshal(data, &bm); err != nil {
		return nil, err
	}

	return bm, nil
}

func (bm Bookmark) IsInBookmarks(url string) bool {
	for _, bookmarkURL := range bm {
		if url == bookmarkURL {
			return true
		}
	}
	return false
}
