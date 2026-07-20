package history_handler

import (
	"os"
	"path/filepath"
	"testing"

	"ani-tracker/bookmark_handler"
	"ani-tracker/common"
)

func TestInitNilFields(t *testing.T) {
	h := &HistoryFile{}
	if err := h.Init(); err != nil {
		t.Fatal("unexpected error:", err)
	}
	if h.PlaylistURL == nil {
		t.Error("expected PlaylistURL to be initialized")
	}
	if h.ComparingLocal == nil {
		t.Error("expected ComparingLocal to be initialized")
	}
}

func TestInitExistingFields(t *testing.T) {
	h := &HistoryFile{
		PlaylistURL:    &common.PlaylistURL{},
		ComparingLocal: &common.ComparingData{},
	}
	if err := h.Init(); err != nil {
		t.Fatal("unexpected error:", err)
	}
}

func TestLoadPlaylists(t *testing.T) {
	h := &HistoryFile{}
	h.Init()
	h.jsonStr = `{
		"playlists": [
			{"playlist_url": "https://youtube.com/p1", "videos": "[{\"video_title\":\"A\",\"video_url\":\"url/1\"}]"},
			{"playlist_url": "https://youtube.com/p2", "videos": "[{\"video_title\":\"B\",\"video_url\":\"url/2\"}]"}
		]
	}`
	if err := h.LoadPlaylists(); err != nil {
		t.Fatal("unexpected error:", err)
	}
	if len(h.PlaylistURL.PlaylistURLs) != 2 {
		t.Fatalf("expected 2 playlist URLs, got %d", len(h.PlaylistURL.PlaylistURLs))
	}
	if h.PlaylistURL.PlaylistURLs[0] != "https://youtube.com/p1" {
		t.Errorf("expected first URL 'https://youtube.com/p1', got %q", h.PlaylistURL.PlaylistURLs[0])
	}
	if len(h.videos) != 2 {
		t.Fatalf("expected 2 video JSON strings, got %d", len(h.videos))
	}
}

func TestLoadPlaylistsEmpty(t *testing.T) {
	h := &HistoryFile{}
	h.Init()
	h.jsonStr = `{"playlists": []}`
	if err := h.LoadPlaylists(); err != nil {
		t.Fatal("unexpected error:", err)
	}
	if len(h.PlaylistURL.PlaylistURLs) != 0 {
		t.Errorf("expected 0 playlist URLs, got %d", len(h.PlaylistURL.PlaylistURLs))
	}
}

func TestFilterPlaylistsByBookmarks(t *testing.T) {
	h := &HistoryFile{
		Bookmarks: bookmark_handler.Bookmark{
			"anime1": "https://youtube.com/p1",
		},
	}
	allPlaylists := []string{"https://youtube.com/p1", "https://youtube.com/p2"}
	allVideos := []string{"[v1]", "[v2]"}
	filteredPlaylists, filteredVideos := h.filterPlaylistsByBookmarks(allPlaylists, allVideos)
	if len(filteredPlaylists) != 1 {
		t.Fatalf("expected 1 filtered playlist, got %d", len(filteredPlaylists))
	}
	if filteredPlaylists[0] != "https://youtube.com/p1" {
		t.Errorf("expected filtered URL 'https://youtube.com/p1', got %q", filteredPlaylists[0])
	}
	if filteredVideos[0] != "[v1]" {
		t.Errorf("expected filtered videos '[v1]', got %q", filteredVideos[0])
	}
}

func TestFilterPlaylistsByBookmarksNoMatch(t *testing.T) {
	h := &HistoryFile{
		Bookmarks: bookmark_handler.Bookmark{
			"anime1": "https://youtube.com/p3",
		},
	}
	allPlaylists := []string{"https://youtube.com/p1"}
	allVideos := []string{"[v1]"}
	filteredPlaylists, filteredVideos := h.filterPlaylistsByBookmarks(allPlaylists, allVideos)
	if len(filteredPlaylists) != 0 {
		t.Errorf("expected 0 filtered playlists, got %d", len(filteredPlaylists))
	}
	if len(filteredVideos) != 0 {
		t.Errorf("expected 0 filtered videos, got %d", len(filteredVideos))
	}
}

func TestLoadPlaylistsWithBookmarks(t *testing.T) {
	h := &HistoryFile{}
	h.Init()
	h.UseBookmarksOnly = true
	h.Bookmarks = bookmark_handler.Bookmark{
		"anime1": "https://youtube.com/p1",
	}
	h.jsonStr = `{
		"playlists": [
			{"playlist_url": "https://youtube.com/p1", "videos": "[{\"video_title\":\"A\",\"video_url\":\"url/1\"}]"},
			{"playlist_url": "https://youtube.com/p2", "videos": "[{\"video_title\":\"B\",\"video_url\":\"url/2\"}]"}
		]
	}`
	if err := h.LoadPlaylists(); err != nil {
		t.Fatal("unexpected error:", err)
	}
	if len(h.PlaylistURL.PlaylistURLs) != 1 {
		t.Fatalf("expected 1 bookmarked playlist, got %d", len(h.PlaylistURL.PlaylistURLs))
	}
	if h.PlaylistURL.PlaylistURLs[0] != "https://youtube.com/p1" {
		t.Errorf("expected URL 'https://youtube.com/p1', got %q", h.PlaylistURL.PlaylistURLs[0])
	}
}

func TestParseVideosToCompareList(t *testing.T) {
	h := &HistoryFile{}
	h.Init()
	h.videos = []string{
		`[{"video_title": "EP 1", "video_url": "https://youtube.com/1"}, {"video_title": "EP 2", "video_url": "https://youtube.com/2"}]`,
		`[{"video_title": "EP 3", "video_url": "https://youtube.com/3"}]`,
	}
	if err := h.ParseVideosToCompareList(); err != nil {
		t.Fatal("unexpected error:", err)
	}
	if len(h.ComparingLocal.CompareListLocal) != 2 {
		t.Fatalf("expected 2 playlists in CompareListLocal, got %d", len(h.ComparingLocal.CompareListLocal))
	}
	if len(h.ComparingLocal.CompareListLocal[0]) != 2 {
		t.Errorf("expected 2 videos in first playlist, got %d", len(h.ComparingLocal.CompareListLocal[0]))
	}
	if h.ComparingLocal.CompareListLocal[0][0].Title != "EP 1" {
		t.Errorf("expected title 'EP 1', got %q", h.ComparingLocal.CompareListLocal[0][0].Title)
	}
	if h.ComparingLocal.CompareListLocal[0][1].URL != "https://youtube.com/2" {
		t.Errorf("expected URL 'https://youtube.com/2', got %q", h.ComparingLocal.CompareListLocal[0][1].URL)
	}
	if h.ComparingLocal.CompareListLocal[1][0].Title != "EP 3" {
		t.Errorf("expected title 'EP 3', got %q", h.ComparingLocal.CompareListLocal[1][0].Title)
	}
}

func TestParseVideosToCompareListEmpty(t *testing.T) {
	h := &HistoryFile{}
	h.Init()
	h.videos = []string{`[]`}
	if err := h.ParseVideosToCompareList(); err != nil {
		t.Fatal("unexpected error:", err)
	}
	if len(h.ComparingLocal.CompareListLocal) != 1 {
		t.Fatalf("expected 1 playlist, got %d", len(h.ComparingLocal.CompareListLocal))
	}
	if len(h.ComparingLocal.CompareListLocal[0]) != 0 {
		t.Errorf("expected 0 videos, got %d", len(h.ComparingLocal.CompareListLocal[0]))
	}
}

func TestGetCompareList(t *testing.T) {
	h := &HistoryFile{}
	h.Init()
	h.ComparingLocal.CompareListLocal = [][]common.VideoInfo{
		{{Title: "A", URL: "url/1"}},
	}
	result := h.GetCompareList()
	if len(result) != 1 {
		t.Fatalf("expected 1 playlist, got %d", len(result))
	}
	if result[0][0].Title != "A" {
		t.Errorf("expected title 'A', got %q", result[0][0].Title)
	}
}

func TestGenerateCompareList(t *testing.T) {
	h := &HistoryFile{}
	h.FileName = filepath.Join(t.TempDir(), "history.json")
	content := `{
		"playlists": [
			{"playlist_url": "https://youtube.com/p1", "videos": "[{\"video_title\":\"A\",\"video_url\":\"url/1\"}]"}
		]
	}`
	if err := os.WriteFile(h.FileName, []byte(content), 0644); err != nil {
		t.Fatal("failed to write temp file:", err)
	}

	if err := h.GenerateCompareList(); err != nil {
		t.Fatal("unexpected error:", err)
	}
	if len(h.PlaylistURL.PlaylistURLs) != 1 {
		t.Errorf("expected 1 playlist URL, got %d", len(h.PlaylistURL.PlaylistURLs))
	}
	if len(h.ComparingLocal.CompareListLocal) != 1 {
		t.Errorf("expected 1 compare list, got %d", len(h.ComparingLocal.CompareListLocal))
	}
	if h.ComparingLocal.CompareListLocal[0][0].Title != "A" {
		t.Errorf("expected title 'A', got %q", h.ComparingLocal.CompareListLocal[0][0].Title)
	}
}
