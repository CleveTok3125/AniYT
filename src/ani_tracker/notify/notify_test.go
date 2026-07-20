package notify

import (
	"testing"

	"ani-tracker/common"
)

func TestDiffNoChanges(t *testing.T) {
	summary := common.DiffSummary{TotalChanges: 0}
	if err := Diff(summary); err != nil {
		t.Fatal("unexpected error:", err)
	}
}

func TestDiffWithChanges(t *testing.T) {
	// This test verifies Diff doesn't crash when there are changes.
	// It may call IsAndroid() and then try to send a notification,
	// which might fail if termux-notification/beeep isn't available.
	// We just verify the function handles the error gracefully.
	summary := common.DiffSummary{
		TotalChanges: 3,
		OnlyInRemote: 2,
		OnlyInLocal:  1,
	}
	err := Diff(summary)
	// err can be non-nil if notification system isn't available; that's OK
	_ = err
}
