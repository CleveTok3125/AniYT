package common

import "testing"

func TestVideoInfoCreation(t *testing.T) {
	v := VideoInfo{Title: "EP 1", URL: "https://youtube.com/1"}
	if v.Title != "EP 1" {
		t.Errorf("expected Title 'EP 1', got %q", v.Title)
	}
	if v.URL != "https://youtube.com/1" {
		t.Errorf("expected URL 'https://youtube.com/1', got %q", v.URL)
	}
}

func TestPlaylistURL(t *testing.T) {
	p := PlaylistURL{PlaylistURLs: []string{"https://youtube.com/p1", "https://youtube.com/p2"}}
	if len(p.PlaylistURLs) != 2 {
		t.Errorf("expected 2 URLs, got %d", len(p.PlaylistURLs))
	}
}

func TestComparingData(t *testing.T) {
	d := ComparingData{
		CompareListLocal:    [][]VideoInfo{{{Title: "A", URL: "url/1"}}},
		ComparingListRemote: [][]VideoInfo{{{Title: "B", URL: "url/2"}}},
	}
	if len(d.CompareListLocal[0]) != 1 {
		t.Errorf("expected 1 local video, got %d", len(d.CompareListLocal[0]))
	}
	if d.ComparingListRemote[0][0].Title != "B" {
		t.Errorf("expected remote title 'B', got %q", d.ComparingListRemote[0][0].Title)
	}
}

func TestGlobalDiffEmpty(t *testing.T) {
	d := GlobalDiff{}
	total := len(d.OnlyInLocal) + len(d.OnlyInRemote) + len(d.TitleChanged)
	if total != 0 {
		t.Errorf("expected 0 total changes, got %d", total)
	}
}

func TestGlobalDiffWithItems(t *testing.T) {
	d := GlobalDiff{
		OnlyInLocal:  []VideoInfo{{Title: "L1", URL: "url/l1"}},
		OnlyInRemote: []VideoInfo{{Title: "R1", URL: "url/r1"}},
		TitleChanged: []TitleChange{{URL: "url/t", OldTitle: "Old", NewTitle: "New"}},
	}
	total := len(d.OnlyInLocal) + len(d.OnlyInRemote) + len(d.TitleChanged)
	if total != 3 {
		t.Errorf("expected 3 total changes, got %d", total)
	}
}

func TestTitleChange(t *testing.T) {
	tc := TitleChange{URL: "url/1", OldTitle: "Old Title", NewTitle: "New Title"}
	if tc.OldTitle != "Old Title" {
		t.Errorf("expected OldTitle 'Old Title', got %q", tc.OldTitle)
	}
	if tc.NewTitle != "New Title" {
		t.Errorf("expected NewTitle 'New Title', got %q", tc.NewTitle)
	}
}

func TestDiffSummary(t *testing.T) {
	s := DiffSummary{TotalChanges: 5, OnlyInLocal: 2, OnlyInRemote: 2, TitleChanged: 1}
	if s.TotalChanges != 5 {
		t.Errorf("expected TotalChanges 5, got %d", s.TotalChanges)
	}
	if s.OnlyInLocal != 2 {
		t.Errorf("expected OnlyInLocal 2, got %d", s.OnlyInLocal)
	}
}
