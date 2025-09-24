package yt_dlp_handler

import (
	"ani-tracker/common"
	"ani-tracker/history_handler"
	"ani-tracker/json_utils"
	"ani-tracker/os_manager"
	"log"
	"os/exec"
	"strings"
)

type PlaylistHandler struct {
	*common.PlaylistURL
	HistoryHandler  *history_handler.HistoryFile
	ComparingRemote *common.ComparingData
}

func (playlist_handler *PlaylistHandler) Init(historyHandler *history_handler.HistoryFile) {
	if playlist_handler.PlaylistURL == nil {
		playlist_handler.PlaylistURL = historyHandler.PlaylistURL
	}

	if playlist_handler.ComparingRemote == nil {
		playlist_handler.ComparingRemote = &common.ComparingData{}
	}
}

func GetPlaylistVideosInfo(url string) (string, error) {
	if ok, err := os_manager.IsInPATH("yt-dlp"); !ok {
		log.Fatal("yt-dlp not found in PATH: ", err)
	}

	cmd := exec.Command("yt-dlp", "--flat-playlist", "-j", url)
	output, err := cmd.CombinedOutput()

	if err != nil {
		errMsg := err.Error()
		outStr := string(output)

		if strings.Contains(errMsg, "signal: interrupt") ||
			strings.Contains(outStr, "Interrupted by user") ||
			strings.Contains(outStr, "KeyboardInterrupt") {
			log.Println("yt-dlp was interrupted, stopping gracefully.")
			return "", err
		}

		log.Fatalf("yt-dlp error: %v\n%s", err, outStr)
	}

	return string(output), nil
}

func (playlist_handler *PlaylistHandler) ParseVideosToCompareList() error {
	playlistURLs := playlist_handler.PlaylistURL.PlaylistURLs

	for _, playlist_url := range playlistURLs {
		playlistJSON, err := GetPlaylistVideosInfo(playlist_url)
		if err != nil {
			return err
		}

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

	return nil
}

func (playlist_handler *PlaylistHandler) GenerateCompareList() error {
	playlist_handler.Init(playlist_handler.HistoryHandler)
	err := playlist_handler.ParseVideosToCompareList()
	return err
}

func (playlist_handler *PlaylistHandler) GetCompareList() [][]common.VideoInfo {
	return playlist_handler.ComparingRemote.ComparingListRemote
}
