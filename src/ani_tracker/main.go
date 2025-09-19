// Main logic
package main

import (
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

	historyHandler.Load()
	historyHandler.GetPlaylistURLs()

	var videos = yt_dlp_handler.GetPlaylistVideosInfo(historyHandler.PlaylistURLs)
	for _, v := range videos {
		log.Println(v.Title)
		log.Println(v.URL)
	}

}
