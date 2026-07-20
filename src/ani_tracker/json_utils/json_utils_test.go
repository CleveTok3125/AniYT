package json_utils

import "testing"

const testJSON = `{
	"playlists": [
		{"playlist_url": "https://youtube.com/p1"},
		{"playlist_url": "https://youtube.com/p2"}
	]
}`

func TestGetStringArray(t *testing.T) {
	result := GetStringArray(testJSON, "playlists.#.playlist_url")
	if len(result) != 2 {
		t.Fatalf("expected 2 results, got %d", len(result))
	}
	if result[0] != "https://youtube.com/p1" {
		t.Errorf("expected first URL 'https://youtube.com/p1', got %q", result[0])
	}
	if result[1] != "https://youtube.com/p2" {
		t.Errorf("expected second URL 'https://youtube.com/p2', got %q", result[1])
	}
}

func TestGetStringArrayEmpty(t *testing.T) {
	result := GetStringArray(`{}`, "playlists.#.playlist_url")
	if len(result) != 0 {
		t.Errorf("expected 0 results, got %d", len(result))
	}
}

func TestGetStringArrayNoMatch(t *testing.T) {
	result := GetStringArray(testJSON, "nonexistent.#.path")
	if len(result) != 0 {
		t.Errorf("expected 0 results, got %d", len(result))
	}
}

func TestParseMultipleJSON_SingleLine(t *testing.T) {
	input := `{"title": "EP 1", "url": "https://youtube.com/1"}`
	result, err := ParseMultipleJSON(input)
	if err != nil {
		t.Fatal("unexpected error:", err)
	}
	if len(result) != 1 {
		t.Fatalf("expected 1 result, got %d", len(result))
	}
}

func TestParseMultipleJSON_MultipleLines(t *testing.T) {
	input := `{"title": "EP 1", "url": "https://youtube.com/1"}
{"title": "EP 2", "url": "https://youtube.com/2"}`
	result, err := ParseMultipleJSON(input)
	if err != nil {
		t.Fatal("unexpected error:", err)
	}
	if len(result) != 2 {
		t.Fatalf("expected 2 results, got %d", len(result))
	}
}

func TestParseMultipleJSON_WithEmptyLines(t *testing.T) {
	input := `{"title": "EP 1", "url": "https://youtube.com/1"}

{"title": "EP 2", "url": "https://youtube.com/2"}`
	result, err := ParseMultipleJSON(input)
	if err != nil {
		t.Fatal("unexpected error:", err)
	}
	if len(result) != 2 {
		t.Fatalf("expected 2 results, got %d", len(result))
	}
}

func TestParseMultipleJSON_EmptyInput(t *testing.T) {
	result, err := ParseMultipleJSON("")
	if err != nil {
		t.Fatal("unexpected error:", err)
	}
	if len(result) != 0 {
		t.Errorf("expected 0 results, got %d", len(result))
	}
}

func TestParseMultipleJSON_InvalidJSON(t *testing.T) {
	_, err := ParseMultipleJSON(`{invalid}`)
	if err == nil {
		t.Fatal("expected error for invalid JSON, got nil")
	}
}
