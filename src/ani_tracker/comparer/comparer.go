package comparer

import (
	"ani-tracker/common"
	"ani-tracker/os_manager"
	"bufio"
	"fmt"
	"log"
	"os"
	"sort"
	"strings"

	"github.com/fatih/color"
)

type DiffFile struct {
	FileName   string
	HasChanges bool
	Summary    common.DiffSummary
}

func (df *DiffFile) GetGlobalDiff(localLists, remoteLists [][]common.VideoInfo) (common.GlobalDiff, common.DiffSummary) {
	localTotal := 0
	for _, pl := range localLists {
		localTotal += len(pl)
	}
	remoteTotal := 0
	for _, pl := range remoteLists {
		remoteTotal += len(pl)
	}

	diff := common.GlobalDiff{
		OnlyInLocal:  make([]common.VideoInfo, 0, localTotal),
		OnlyInRemote: make([]common.VideoInfo, 0, remoteTotal),
		TitleChanged: make([]common.TitleChange, 0, min(localTotal, remoteTotal)),
	}

	localSet := make(map[string]common.VideoInfo, localTotal)
	for _, pl := range localLists {
		for _, v := range pl {
			localSet[v.URL] = v
		}
	}

	remoteSet := make(map[string]common.VideoInfo, remoteTotal)
	for _, pl := range remoteLists {
		for _, v := range pl {
			remoteSet[v.URL] = v
		}
	}

	for url, lv := range localSet {
		if rv, exists := remoteSet[url]; !exists {
			diff.OnlyInLocal = append(diff.OnlyInLocal, lv)
		} else if lv.Title != rv.Title {
			diff.TitleChanged = append(diff.TitleChanged, common.TitleChange{
				URL:      url,
				OldTitle: lv.Title,
				NewTitle: rv.Title,
			})
		}
	}

	for url, rv := range remoteSet {
		if _, exists := localSet[url]; !exists {
			diff.OnlyInRemote = append(diff.OnlyInRemote, rv)
		}
	}

	sort.Slice(diff.OnlyInLocal, func(i, j int) bool {
		return diff.OnlyInLocal[i].Title < diff.OnlyInLocal[j].Title
	})
	sort.Slice(diff.OnlyInRemote, func(i, j int) bool {
		return diff.OnlyInRemote[i].Title < diff.OnlyInRemote[j].Title
	})
	sort.Slice(diff.TitleChanged, func(i, j int) bool {
		return diff.TitleChanged[i].NewTitle < diff.TitleChanged[j].NewTitle
	})

	summary := common.DiffSummary{
		TotalChanges: len(diff.OnlyInLocal) + len(diff.OnlyInRemote) + len(diff.TitleChanged),
		OnlyInLocal:  len(diff.OnlyInLocal),
		OnlyInRemote: len(diff.OnlyInRemote),
		TitleChanged: len(diff.TitleChanged),
	}

	df.HasChanges = summary.TotalChanges > 0
	df.Summary = summary

	return diff, summary
}

func (df *DiffFile) ExportGlobalDiffToFile(diff common.GlobalDiff, summary common.DiffSummary, fileName string) error {
	if !df.HasChanges {
		log.Println("No changes made, no file exported")
		return nil
	}

	f, err := os.Create(fileName)
	if err != nil {
		return err
	}
	defer f.Close()

	_, err = fmt.Fprintf(f,
		"=== Diff Local vs Remote ===\n\nTotal changes: %d\n+ Added: %d\n- Deleted: %d\n* Renamed: %d\n\n",
		summary.TotalChanges,
		summary.OnlyInRemote,
		summary.OnlyInLocal,
		summary.TitleChanged,
	)
	if err != nil {
		return err
	}

	_, err = f.WriteString("Only in Remote:\n")
	if err != nil {
		return err
	}
	for _, v := range diff.OnlyInRemote {
		if _, err := fmt.Fprintf(f, "+ %s\n  %s\n", v.Title, v.URL); err != nil {
			return err
		}
	}

	_, err = f.WriteString("\nOnly in Local:\n")
	if err != nil {
		return err
	}
	for _, v := range diff.OnlyInLocal {
		if _, err := fmt.Fprintf(f, "- %s\n  %s\n", v.Title, v.URL); err != nil {
			return err
		}
	}

	_, err = f.WriteString("\nTitle Changed:\n")
	if err != nil {
		return err
	}
	for _, t := range diff.TitleChanged {
		if _, err := fmt.Fprintf(f, "* %s\n  - %s\n  + %s\n", t.URL, t.OldTitle, t.NewTitle); err != nil {
			return err
		}
	}

	log.Printf("Global diff exported to: \"%s\"", os_manager.GetAbsPath(df.FileName))

	return nil
}

func (df *DiffFile) Diff(localLists, remoteLists [][]common.VideoInfo) {

	diff, summary := df.GetGlobalDiff(
		localLists,
		remoteLists,
	)

	if err := df.ExportGlobalDiffToFile(diff, summary, df.FileName); err != nil {
		log.Println("Diff export failed:", err)
		return
	}
}

func ShowDiff(file string) {
	err := printDiffColored(file)
	if err != nil {
		fmt.Println("Error reading diff file:", err)
	}
}

func printDiffColored(file string) error {
	f, err := os.Open(file)
	if err != nil {
		return err
	}
	defer f.Close()

	prefixColors := []struct {
		prefix string
		color  func(a ...any) string
	}{
		{"=== Diff Local vs Remote ===", color.New(color.FgCyan, color.Bold).SprintFunc()},
		{"Total changes:", color.New(color.FgYellow).SprintFunc()},
		{"+ Added:", color.New(color.FgGreen).SprintFunc()},
		{"- Deleted:", color.New(color.FgRed).SprintFunc()},
		{"* Renamed:", color.New(color.FgHiYellow).SprintFunc()},
		{"  http", color.New(color.FgHiBlue).SprintFunc()},
		{"  -", color.New(color.FgRed).SprintFunc()},
		{"  +", color.New(color.FgGreen).SprintFunc()},
		{"Only in Local:", color.New(color.FgCyan, color.Bold).SprintFunc()},
		{"Only in Remote:", color.New(color.FgCyan, color.Bold).SprintFunc()},
		{"Title Changed:", color.New(color.FgCyan, color.Bold).SprintFunc()},
	}

	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Text()
		colored := false

		for _, pc := range prefixColors {
			if strings.HasPrefix(line, pc.prefix) {
				fmt.Println(pc.color(line))
				colored = true
				break
			}
		}

		if !colored {
			switch {
			case strings.HasPrefix(line, "+"):
				color.Green(line)
			case strings.HasPrefix(line, "-"):
				color.Red(line)
			case strings.HasPrefix(line, "*"):
				color.HiYellow(line)
			default:
				fmt.Println(line)
			}
		}
	}

	return scanner.Err()
}
