package yt_dlp_handler

import (
	"ani-tracker/json_utils"
	"log"
	"os/exec"
)

type VideoInfo struct {
	Title string
	URL   string
}

func GetPlaylistVideos(url string) string {
	cmd := exec.Command("yt-dlp", "--flat-playlist", "-j", url)
	output, err := cmd.CombinedOutput()

	if err != nil {
		log.Fatalf("yt-dlp error: %v\n%s", err, string(output))
	}

	return string(output)
}

func GetPlaylistVideosInfo(PlaylistURLs []string) []VideoInfo {
	var videos []VideoInfo

	for _, playlist_url := range PlaylistURLs {
		playlistJSON := GetPlaylistVideos(playlist_url)
		playlistObjs := json_utils.ParseMultipleJSON(playlistJSON)
		titles := json_utils.GetBytesStringArray(playlistObjs, "#.title")
		urls := json_utils.GetBytesStringArray(playlistObjs, "#.url")

		for i := range titles {
			videos = append(videos, VideoInfo{
				Title: titles[i],
				URL:   urls[i],
			})
		}
	}

	return videos
}
