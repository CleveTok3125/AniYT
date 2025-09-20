package yt_dlp_handler

import (
	"ani-tracker/common"
	"ani-tracker/history_handler"
	"ani-tracker/json_utils"
	"log"
	"os/exec"
)

type PlaylistHandler struct {
	*common.PlaylistURL
	ComparingRemote *common.Comparing
}

func (playlist_handler *PlaylistHandler) Init(historyHandler *history_handler.HistoryFile) {
	if playlist_handler.PlaylistURL == nil {
		playlist_handler.PlaylistURL = historyHandler.PlaylistURL
	}

	if playlist_handler.ComparingRemote == nil {
		playlist_handler.ComparingRemote = &common.Comparing{}
	}
}

func GetPlaylistVideosInfo(url string) string {
	cmd := exec.Command("yt-dlp", "--flat-playlist", "-j", url)
	output, err := cmd.CombinedOutput()

	if err != nil {
		log.Fatalf("yt-dlp error: %v\n%s", err, string(output))
	}

	return string(output)
}

func (playlist_handler *PlaylistHandler) ParseVideosToCompareList() {
	playlistURLs := playlist_handler.PlaylistURL.PlaylistURLs

	for _, playlist_url := range playlistURLs {
		playlistJSON := GetPlaylistVideosInfo(playlist_url)
		videos := make([]common.VideoInfo, 0)

		parsedJson, err := json_utils.ParseMultipleJSON(playlistJSON)

		if err != nil {
			log.Fatalf("Failed to parse JSON: %v", err)
		}

		for _, obj := range parsedJson {
			m := obj.(map[string]any)
			title, _ := m["title"].(string)
			url, _ := m["url"].(string)
			videos = append(videos, common.VideoInfo{
				Title: title,
				URL:   url,
			})
		}

		playlist_handler.ComparingRemote.ComparingListRemote = append(playlist_handler.ComparingRemote.ComparingListRemote, videos)
	}
}
