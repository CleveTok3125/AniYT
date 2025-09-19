package history_handler

import (
	"ani-tracker/json_utils"
	"fmt"
	"os"
	"reflect"
)

type HistoryHandler interface {
	Load() []string
}

type HistoryFile struct {
	FileName     string
	JsonStr      string
	PlaylistURLs []string
}

func (history_handler *HistoryFile) GetField(fieldName string) any {
	refl := reflect.ValueOf(history_handler).Elem()
	field := refl.FieldByName(fieldName)
	if !field.IsValid() {
		fmt.Println("Warning: Field not found:", fieldName)
	}
	return field.Interface()
}

func (history_file *HistoryFile) Load() {
	data, err := os.ReadFile(history_file.FileName)

	if err != nil {
		fmt.Println("Error reading history.json:", err)
		os.Exit(1)
	}

	history_file.JsonStr = string(data)
}

func (history_handler *HistoryFile) GetPlaylistURLs() {
	history_handler.PlaylistURLs = json_utils.GetStringArray(history_handler.JsonStr, "playlists.#.playlist_url")
}
