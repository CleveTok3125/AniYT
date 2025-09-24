package history_handler

import (
	"ani-tracker/common"
	"ani-tracker/json_utils"
	"encoding/json"
	"log"
	"os"
)

type HistoryHandler any

type HistoryFile struct {
	*common.PlaylistURL
	ComparingLocal *common.ComparingData
	FileName       string
	jsonStr        string
	videos         []string
}

func (history_handler *HistoryFile) Init() error {
	if history_handler.PlaylistURL == nil {
		history_handler.PlaylistURL = &common.PlaylistURL{}

	}

	if history_handler.ComparingLocal == nil {
		history_handler.ComparingLocal = &common.ComparingData{}
	}
	return nil
}

func (history_file *HistoryFile) Load() error {
	data, err := os.ReadFile(history_file.FileName)

	if err != nil {
		log.Fatal("Error reading history.json:", err)
	}

	history_file.jsonStr = string(data)
	return nil
}

func (history_handler *HistoryFile) LoadPlaylists() error {
	history_handler.PlaylistURL.PlaylistURLs = json_utils.GetStringArray(history_handler.jsonStr, "playlists.#.playlist_url")
	history_handler.videos = json_utils.GetStringArray(history_handler.jsonStr, "playlists.#.videos")
	history_handler.jsonStr = "" // GC
	return nil
}

func (history_handler *HistoryFile) ParseVideosToCompareList() error {
	for _, v := range history_handler.videos {
		var videoObjs []map[string]any
		if err := json.Unmarshal([]byte(v), &videoObjs); err != nil {
			log.Fatalf("Parse error: %v", err)
		}

		video_list := make([]common.VideoInfo, 0, len(videoObjs))
		for _, obj := range videoObjs {
			title, _ := obj["video_title"].(string)
			url, _ := obj["video_url"].(string)
			video_list = append(video_list, common.VideoInfo{
				Title: title,
				URL:   url,
			})
		}
		history_handler.ComparingLocal.CompareListLocal = append(history_handler.ComparingLocal.CompareListLocal, video_list)
	}

	history_handler.videos = nil // GC
	return nil
}

func (history_handler *HistoryFile) GenerateCompareList() error {
	steps := []func() error{
		history_handler.Init,
		history_handler.Load,
		history_handler.LoadPlaylists,
		history_handler.ParseVideosToCompareList,
	}

	for _, step := range steps {
		err := step()
		if err != nil {
			return err
		}
	}
	return nil
}

func (history_handler *HistoryFile) GetCompareList() [][]common.VideoInfo {
	return history_handler.ComparingLocal.CompareListLocal
}
