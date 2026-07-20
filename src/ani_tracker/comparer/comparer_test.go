package comparer

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"ani-tracker/common"
)

func TestGetGlobalDiff_NoChanges(t *testing.T) {
	df := &DiffFile{}
	local := [][]common.VideoInfo{
		{{Title: "A", URL: "url/1"}, {Title: "B", URL: "url/2"}},
	}
	remote := [][]common.VideoInfo{
		{{Title: "A", URL: "url/1"}, {Title: "B", URL: "url/2"}},
	}

	diff, summary := df.GetGlobalDiff(local, remote)
	if df.HasChanges {
		t.Error("expected HasChanges to be false")
	}
	if summary.TotalChanges != 0 {
		t.Errorf("expected 0 total changes, got %d", summary.TotalChanges)
	}
	if len(diff.OnlyInLocal) != 0 {
		t.Errorf("expected 0 OnlyInLocal, got %d", len(diff.OnlyInLocal))
	}
	if len(diff.OnlyInRemote) != 0 {
		t.Errorf("expected 0 OnlyInRemote, got %d", len(diff.OnlyInRemote))
	}
	if len(diff.TitleChanged) != 0 {
		t.Errorf("expected 0 TitleChanged, got %d", len(diff.TitleChanged))
	}
}

func TestGetGlobalDiff_OnlyInRemote(t *testing.T) {
	df := &DiffFile{}
	local := [][]common.VideoInfo{
		{{Title: "A", URL: "url/1"}},
	}
	remote := [][]common.VideoInfo{
		{{Title: "A", URL: "url/1"}, {Title: "B", URL: "url/2"}},
	}

	diff, summary := df.GetGlobalDiff(local, remote)
	if !df.HasChanges {
		t.Error("expected HasChanges to be true")
	}
	if summary.OnlyInRemote != 1 {
		t.Errorf("expected 1 OnlyInRemote, got %d", summary.OnlyInRemote)
	}
	if len(diff.OnlyInRemote) != 1 {
		t.Fatalf("expected 1 OnlyInRemote, got %d", len(diff.OnlyInRemote))
	}
	if diff.OnlyInRemote[0].URL != "url/2" {
		t.Errorf("expected OnlyInRemote URL 'url/2', got %q", diff.OnlyInRemote[0].URL)
	}
}

func TestGetGlobalDiff_OnlyInLocal(t *testing.T) {
	df := &DiffFile{}
	local := [][]common.VideoInfo{
		{{Title: "A", URL: "url/1"}, {Title: "B", URL: "url/2"}},
	}
	remote := [][]common.VideoInfo{
		{{Title: "A", URL: "url/1"}},
	}

	diff, summary := df.GetGlobalDiff(local, remote)
	if !df.HasChanges {
		t.Error("expected HasChanges to be true")
	}
	if summary.OnlyInLocal != 1 {
		t.Errorf("expected 1 OnlyInLocal, got %d", summary.OnlyInLocal)
	}
	if len(diff.OnlyInLocal) != 1 {
		t.Fatalf("expected 1 OnlyInLocal, got %d", len(diff.OnlyInLocal))
	}
	if diff.OnlyInLocal[0].URL != "url/2" {
		t.Errorf("expected OnlyInLocal URL 'url/2', got %q", diff.OnlyInLocal[0].URL)
	}
}

func TestGetGlobalDiff_TitleChanged(t *testing.T) {
	df := &DiffFile{}
	local := [][]common.VideoInfo{
		{{Title: "Old Title", URL: "url/1"}},
	}
	remote := [][]common.VideoInfo{
		{{Title: "New Title", URL: "url/1"}},
	}

	diff, summary := df.GetGlobalDiff(local, remote)
	if !df.HasChanges {
		t.Error("expected HasChanges to be true")
	}
	if summary.TitleChanged != 1 {
		t.Errorf("expected 1 TitleChanged, got %d", summary.TitleChanged)
	}
	if len(diff.TitleChanged) != 1 {
		t.Fatalf("expected 1 TitleChanged, got %d", len(diff.TitleChanged))
	}
	if diff.TitleChanged[0].URL != "url/1" {
		t.Errorf("expected URL 'url/1', got %q", diff.TitleChanged[0].URL)
	}
	if diff.TitleChanged[0].OldTitle != "Old Title" {
		t.Errorf("expected OldTitle 'Old Title', got %q", diff.TitleChanged[0].OldTitle)
	}
	if diff.TitleChanged[0].NewTitle != "New Title" {
		t.Errorf("expected NewTitle 'New Title', got %q", diff.TitleChanged[0].NewTitle)
	}
}

func TestGetGlobalDiff_MultiplePlaylists(t *testing.T) {
	df := &DiffFile{}
	local := [][]common.VideoInfo{
		{{Title: "A", URL: "url/1"}},
		{{Title: "B", URL: "url/2"}},
	}
	remote := [][]common.VideoInfo{
		{{Title: "A", URL: "url/1"}},
		{{Title: "C", URL: "url/3"}},
	}

	diff, summary := df.GetGlobalDiff(local, remote)
	if !df.HasChanges {
		t.Error("expected HasChanges to be true")
	}
	if summary.OnlyInLocal != 1 {
		t.Errorf("expected 1 OnlyInLocal, got %d", summary.OnlyInLocal)
	}
	if summary.OnlyInRemote != 1 {
		t.Errorf("expected 1 OnlyInRemote, got %d", summary.OnlyInRemote)
	}
	if len(diff.OnlyInLocal) != 1 || diff.OnlyInLocal[0].URL != "url/2" {
		t.Errorf("expected OnlyInLocal 'url/2', got %v", diff.OnlyInLocal)
	}
	if len(diff.OnlyInRemote) != 1 || diff.OnlyInRemote[0].URL != "url/3" {
		t.Errorf("expected OnlyInRemote 'url/3', got %v", diff.OnlyInRemote)
	}
}

func TestGetGlobalDiff_SortedByTitle(t *testing.T) {
	df := &DiffFile{}
	local := [][]common.VideoInfo{}
	remote := [][]common.VideoInfo{
		{{Title: "Z Video", URL: "url/z"}, {Title: "A Video", URL: "url/a"}},
	}

	diff, _ := df.GetGlobalDiff(local, remote)
	if len(diff.OnlyInRemote) != 2 {
		t.Fatalf("expected 2 OnlyInRemote, got %d", len(diff.OnlyInRemote))
	}
	// Should be sorted by title: "A Video" first, then "Z Video"
	if diff.OnlyInRemote[0].Title != "A Video" {
		t.Errorf("expected first sorted title 'A Video', got %q", diff.OnlyInRemote[0].Title)
	}
	if diff.OnlyInRemote[1].Title != "Z Video" {
		t.Errorf("expected second sorted title 'Z Video', got %q", diff.OnlyInRemote[1].Title)
	}
}

func TestExportGlobalDiffToFile_NoChanges(t *testing.T) {
	df := &DiffFile{HasChanges: false}
	diff := common.GlobalDiff{}
	summary := common.DiffSummary{}
	tmpDir := t.TempDir()
	fileName := filepath.Join(tmpDir, "diff.txt")

	err := df.ExportGlobalDiffToFile(diff, summary, fileName)
	if err != nil {
		t.Fatal("unexpected error:", err)
	}
	if _, err := os.Stat(fileName); !os.IsNotExist(err) {
		t.Error("expected no file to be created when HasChanges is false")
	}
}

func TestExportGlobalDiffToFile_WithChanges(t *testing.T) {
	df := &DiffFile{HasChanges: true}
	diff := common.GlobalDiff{
		OnlyInRemote: []common.VideoInfo{{Title: "New Video", URL: "https://youtube.com/new"}},
		OnlyInLocal:  []common.VideoInfo{{Title: "Removed Video", URL: "https://youtube.com/old"}},
		TitleChanged: []common.TitleChange{
			{URL: "https://youtube.com/changed", OldTitle: "Old", NewTitle: "New"},
		},
	}
	summary := common.DiffSummary{
		TotalChanges: 3, OnlyInRemote: 1, OnlyInLocal: 1, TitleChanged: 1,
	}
	tmpDir := t.TempDir()
	fileName := filepath.Join(tmpDir, "diff.txt")

	err := df.ExportGlobalDiffToFile(diff, summary, fileName)
	if err != nil {
		t.Fatal("unexpected error:", err)
	}
	data, err := os.ReadFile(fileName)
	if err != nil {
		t.Fatal("failed to read diff file:", err)
	}
	content := string(data)
	if !contains(content, "Total changes: 3") {
		t.Error("expected 'Total changes: 3' in output")
	}
	if !contains(content, "+ Added: 1") {
		t.Error("expected '+ Added: 1' in output")
	}
	if !contains(content, "- Deleted: 1") {
		t.Error("expected '- Deleted: 1' in output")
	}
	if !contains(content, "* Renamed: 1") {
		t.Error("expected '* Renamed: 1' in output")
	}
}

func contains(s, substr string) bool {
	return strings.Contains(s, substr)
}
