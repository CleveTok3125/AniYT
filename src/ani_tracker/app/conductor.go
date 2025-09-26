package app

import (
	"ani-tracker/bookmark_handler"
	"ani-tracker/common"
	"ani-tracker/comparer"
	"ani-tracker/history_handler"
	"ani-tracker/notify"
	"ani-tracker/yt_dlp_handler"
	"log"
)

type Config struct {
	HistoryFileName  string
	BookmarkFileName string
	DiffFileName     string
	UseBookmarksOnly bool
	Silent           bool
}

func (cfg *Config) Conductor() error {
	historyHandler := &history_handler.HistoryFile{FileName: cfg.HistoryFileName, UseBookmarksOnly: cfg.UseBookmarksOnly}

	if cfg.UseBookmarksOnly {
		bm, err := bookmark_handler.LoadBookmarkFromFile(cfg.BookmarkFileName)
		if err != nil {
			log.Printf("Load bookmarks failed: %v", err)
			return err
		}
		historyHandler.Bookmarks = bm
	}

	ytdlpHandler := &yt_dlp_handler.PlaylistHandler{HistoryHandler: historyHandler}
	cmp := &comparer.DiffFile{FileName: cfg.DiffFileName}

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

	if !cfg.Silent && cmp.HasChanges {
		notify.NotifyDiff(cmp.Summary)
	}

	return nil
}
