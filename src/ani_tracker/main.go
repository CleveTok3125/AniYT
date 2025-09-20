// Main logic
package main

import (
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

	historyHandler := &history_handler.HistoryFile{
		FileName: "history.json",
	}
	ytdlpHandler := &yt_dlp_handler.PlaylistHandler{}

	historyHandler.Init()
	historyHandler.Load()
	historyHandler.GenerateCompareList()

	ytdlpHandler.Init(historyHandler)
	ytdlpHandler.ParseVideosToCompareList()

	debug_utils.PrettyDump(historyHandler.ComparingLocal.CompareListLocal, "    ")
	log.Print("\n\n\n")
	debug_utils.PrettyDump(ytdlpHandler.ComparingRemote.ComparingListRemote, "    ")
}
