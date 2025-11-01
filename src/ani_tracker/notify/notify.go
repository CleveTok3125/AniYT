// Package notify Send notifications to users
package notify

import (
	"ani-tracker/common"
	"ani-tracker/os_manager"
	"fmt"
	"os/exec"

	"github.com/gen2brain/beeep"
)

func notifyTermux(title, message string) error {
	cmd := exec.Command("termux-notification",
		"--title", title,
		"--content", message,
	)
	return cmd.Run()
}

// Diff Send notifications about changes in data to users
func Diff(summary common.DiffSummary) error {
	if summary.TotalChanges == 0 {
		return nil
	}

	title := "Ani-Tracker: Video Updates Available!"

	lines := []string{fmt.Sprintf("%d video(s) need update:", summary.TotalChanges)}

	if summary.OnlyInRemote > 0 {
		lines = append(lines, fmt.Sprintf("\t• New added:\t%d", summary.OnlyInRemote))
	}
	if summary.OnlyInLocal > 0 {
		lines = append(lines, fmt.Sprintf("\t• Removed:\t%d", summary.OnlyInLocal))
	}
	if summary.TitleChanged > 0 {
		lines = append(lines, fmt.Sprintf("\t• Renamed:\t%d", summary.TitleChanged))
	}

	message := ""
	for _, line := range lines {
		message += line + "\n"
	}

	if os_manager.IsAndroid() {
		return notifyTermux(title, message)
	}
	return beeep.Notify(title, message, "")
}
