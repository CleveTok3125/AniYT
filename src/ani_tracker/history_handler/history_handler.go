package history_handler

import (
	"ani-tracker/json_utils"
	"log"
	"os"
)

type HistoryHandler any

type HistoryFile struct {
	FileName     string
	JsonStr      string
	PlaylistURLs []string
	Videos       []string
	CompareList  [][]VideosInfo
}

type VideosInfo struct {
	Title string `json:"video_title"`
	URL   string `json:"video_url"`
}

func (history_file *HistoryFile) Load() {
	data, err := os.ReadFile(history_file.FileName)

	if err != nil {
		log.Fatal("Error reading history.json:", err)
	}

	history_file.JsonStr = string(data)
}

func (history_handler *HistoryFile) GetPlaylistURLs() {
	history_handler.PlaylistURLs = json_utils.GetStringArray(history_handler.JsonStr, "playlists.#.playlist_url")
}

func (history_handler *HistoryFile) GetPlaylistVideos() {
	history_handler.Videos = json_utils.GetStringArray(history_handler.JsonStr, "playlists.#.videos")
}

func (history_handler *HistoryFile) ParseVideosToCompareList() {
	for _, v := range history_handler.Videos {
		var video_list []VideosInfo
		for idx := range json_utils.GetJSONValueCount(v, "video_title") {
			title := json_utils.GetJSONValueAt(v, "video_title", idx).(string)
			url := json_utils.GetJSONValueAt(v, "video_url", idx).(string)
			video_list = append(video_list, VideosInfo{
				Title: title,
				URL:   url,
			})
		}
		history_handler.CompareList = append(history_handler.CompareList, video_list)
	}
}
