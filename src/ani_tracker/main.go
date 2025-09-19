package main

import (
	"ani-tracker/history_handler"
	"ani-tracker/yt_dlp_handler"
	"log"
	"os"
)

func main() {
	os.Chdir("../../data")

	history_handler := &history_handler.HistoryFile{
		FileName: "history.json",
	}

	history_handler.Load()
	history_handler.GetPlaylistURLs()

	var videos []yt_dlp_handler.VideoInfo = yt_dlp_handler.GetPlaylistVideosInfo(history_handler.PlaylistURLs)
	for _, v := range videos {
		log.Println(v.Title)
		log.Println(v.URL)
	}
}
