package bookmark_handler

import (
	"os"
	"testing"
)

func TestIsInBookmarks(t *testing.T) {
	bm := Bookmark{
		"anime1": "https://youtube.com/playlist?list=PL1",
		"anime2": "https://youtube.com/playlist?list=PL2",
	}

	if !bm.IsInBookmarks("https://youtube.com/playlist?list=PL1") {
		t.Error("expected PL1 to be in bookmarks")
	}
	if !bm.IsInBookmarks("https://youtube.com/playlist?list=PL2") {
		t.Error("expected PL2 to be in bookmarks")
	}
	if bm.IsInBookmarks("https://youtube.com/playlist?list=PL3") {
		t.Error("expected PL3 NOT to be in bookmarks")
	}
}

func TestIsInBookmarksEmpty(t *testing.T) {
	bm := Bookmark{}
	if bm.IsInBookmarks("https://youtube.com/any") {
		t.Error("expected empty bookmarks to return false")
	}
}

func TestLoadBookmarkFromFile(t *testing.T) {
	content := `{"anime1": "https://youtube.com/playlist?list=PL1"}`
	tmpFile, err := os.CreateTemp(t.TempDir(), "bookmark_*.json")
	if err != nil {
		t.Fatal("failed to create temp file:", err)
	}
	if _, err := tmpFile.Write([]byte(content)); err != nil {
		t.Fatal("failed to write temp file:", err)
	}
	tmpFile.Close()

	bm, err := LoadBookmarkFromFile(tmpFile.Name())
	if err != nil {
		t.Fatal("unexpected error:", err)
	}
	if len(bm) != 1 {
		t.Fatalf("expected 1 bookmark, got %d", len(bm))
	}
	if bm["anime1"] != "https://youtube.com/playlist?list=PL1" {
		t.Errorf("expected URL 'https://youtube.com/playlist?list=PL1', got %q", bm["anime1"])
	}
}

func TestLoadBookmarkFromFile_NotFound(t *testing.T) {
	_, err := LoadBookmarkFromFile("/nonexistent/path/bookmark.json")
	if err == nil {
		t.Fatal("expected error for nonexistent file, got nil")
	}
}

func TestLoadBookmarkFromFile_InvalidJSON(t *testing.T) {
	tmpFile, err := os.CreateTemp(t.TempDir(), "bookmark_*.json")
	if err != nil {
		t.Fatal("failed to create temp file:", err)
	}
	if _, err := tmpFile.Write([]byte("{invalid}")); err != nil {
		t.Fatal("failed to write temp file:", err)
	}
	tmpFile.Close()

	_, err = LoadBookmarkFromFile(tmpFile.Name())
	if err == nil {
		t.Fatal("expected error for invalid JSON, got nil")
	}
}
