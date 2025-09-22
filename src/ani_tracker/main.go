// Main logic
package main

import (
	"ani-tracker/common"
	"ani-tracker/comparer"
	"ani-tracker/debug_utils"
	"ani-tracker/history_handler"
	"ani-tracker/yt_dlp_handler"

	"log"
	"os"
)

func main() {
	err := os.Chdir("../../data")
	if err != nil {
		log.Fatal("Failed to change dir: ", err)
	}

	historyHandler := &history_handler.HistoryFile{FileName: "history.json"}
	ytdlpHandler := &yt_dlp_handler.PlaylistHandler{HistoryHandler: historyHandler}
	cmp := &comparer.DiffFile{FileName: "playlists.diff"}

	handlers := []common.GenerateCompare{
		historyHandler,
		ytdlpHandler,
	}

	for _, handler := range handlers {
		handler.GenerateCompareList()
		debug_utils.PrettyDump(handler.GetCompareList(), "    ")
	}

	cmp.Diff(historyHandler.GetCompareList(), ytdlpHandler.GetCompareList())
}
