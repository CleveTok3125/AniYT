package notify

import (
	"ani-tracker/common"
	"fmt"

	"github.com/gen2brain/beeep"
)

func NotifyDiff(summary common.DiffSummary) error {
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

	return beeep.Notify(title, message, "")
}
