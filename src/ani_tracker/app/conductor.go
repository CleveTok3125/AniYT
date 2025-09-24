package app

import (
	"ani-tracker/common"
	"ani-tracker/comparer"
	"ani-tracker/history_handler"
	"ani-tracker/yt_dlp_handler"
	"log"
)

func Conductor() error {
	historyHandler := &history_handler.HistoryFile{FileName: "history.json"}
	ytdlpHandler := &yt_dlp_handler.PlaylistHandler{HistoryHandler: historyHandler}
	cmp := &comparer.DiffFile{FileName: "playlists.diff"}

	handlers := []common.GenerateCompare{
		historyHandler,
		ytdlpHandler,
	}

	for _, handler := range handlers {
		if err := handler.GenerateCompareList(); err != nil {
			log.Printf("GenerateCompareList failed: %v", err)
			return err
		}
	}

	cmp.Diff(historyHandler.GetCompareList(), ytdlpHandler.GetCompareList())

	return nil
}
