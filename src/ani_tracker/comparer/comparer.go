package comparer

import (
	"ani-tracker/common"
	"fmt"
	"log"
	"os"
	"sort"
)

type DiffFile struct {
	FileName string
}

func GetGlobalDiff(localLists, remoteLists [][]common.VideoInfo) common.GlobalDiff {
	var diff common.GlobalDiff

	localSet := make(map[string]common.VideoInfo)
	for _, pl := range localLists {
		for _, v := range pl {
			localSet[v.URL] = v
		}
	}

	remoteSet := make(map[string]common.VideoInfo)
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

	return diff
}

func ExportGlobalDiffToFile(diff common.GlobalDiff, fileName string) error {
	f, err := os.Create(fileName)
	if err != nil {
		return err
	}
	defer f.Close()

	f.WriteString("=== Diff Local vs Remote ===\n\n")

	f.WriteString("Only in Local:\n")
	for _, v := range diff.OnlyInLocal {
		fmt.Fprintf(f, "- %s (%s)\n", v.Title, v.URL)
	}

	f.WriteString("\nOnly in Remote:\n")
	for _, v := range diff.OnlyInRemote {
		fmt.Fprintf(f, "+ %s (%s)\n", v.Title, v.URL)
	}

	f.WriteString("\nTitle Changed:\n")
	for _, t := range diff.TitleChanged {
		fmt.Fprintf(f, "* %s\n  - Old: %s\n  - New: %s\n", t.URL, t.OldTitle, t.NewTitle)
	}

	return nil
}

func (df *DiffFile) Diff(localLists, remoteLists [][]common.VideoInfo) common.GlobalDiff {

	diff := GetGlobalDiff(
		localLists,
		remoteLists,
	)

	if err := ExportGlobalDiffToFile(diff, df.FileName); err != nil {
		log.Fatal("Failed to export diff:", err)
	}

	log.Printf("Global diff exported to \"%s\"", df.FileName)

	return diff
}
