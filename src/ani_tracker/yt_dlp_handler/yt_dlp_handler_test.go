package yt_dlp_handler

import (
	"testing"

	"ani-tracker/common"
	"ani-tracker/history_handler"
)

func TestInitWithHistoryHandler(t *testing.T) {
	h := &history_handler.HistoryFile{}
	h.Init()
	h.PlaylistURL.PlaylistURLs = []string{"https://youtube.com/p1"}

	p := &PlaylistHandler{}
	p.Init(h)

	if p.ComparingRemote == nil {
		t.Error("expected ComparingRemote to be initialized")
	}
	if len(p.PlaylistURL.PlaylistURLs) != 1 {
		t.Errorf("expected 1 playlist URL, got %d", len(p.PlaylistURL.PlaylistURLs))
	}
	if p.PlaylistURL.PlaylistURLs[0] != "https://youtube.com/p1" {
		t.Errorf("expected URL 'https://youtube.com/p1', got %q", p.PlaylistURL.PlaylistURLs[0])
	}
}

func TestInitWithExistingURLs(t *testing.T) {
	h := &history_handler.HistoryFile{}
	h.Init()
	h.PlaylistURL.PlaylistURLs = []string{"https://youtube.com/p1"}

	p := &PlaylistHandler{
		PlaylistURL: &common.PlaylistURL{
			PlaylistURLs: []string{"https://youtube.com/p2"},
		},
	}
	p.Init(h)

	// Should NOT overwrite existing URLs
	if len(p.PlaylistURL.PlaylistURLs) != 1 {
		t.Errorf("expected 1 playlist URL, got %d", len(p.PlaylistURL.PlaylistURLs))
	}
	if p.PlaylistURL.PlaylistURLs[0] != "https://youtube.com/p2" {
		t.Errorf("expected URL 'https://youtube.com/p2', got %q", p.PlaylistURL.PlaylistURLs[0])
	}
}

func TestGetCompareList(t *testing.T) {
	p := &PlaylistHandler{
		ComparingRemote: &common.ComparingData{
			ComparingListRemote: [][]common.VideoInfo{
				{{Title: "A", URL: "url/1"}},
			},
		},
	}
	result := p.GetCompareList()
	if len(result) != 1 {
		t.Fatalf("expected 1 playlist, got %d", len(result))
	}
	if result[0][0].Title != "A" {
		t.Errorf("expected title 'A', got %q", result[0][0].Title)
	}
}
