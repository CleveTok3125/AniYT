package app

import (
	"ani-tracker/args_handler"
	"ani-tracker/comparer"
	"fmt"
	"os"
	"path/filepath"
)

type NonCrons interface {
	Run(cfg *args_handler.Config)
}

type ShowDiffCmd struct {
	DiffFileName string
}

type KillCmd struct{}

func (c ShowDiffCmd) Run(cfg *args_handler.Config) {
	if !cfg.ShowDiff {
		return
	}

	comparer.ShowDiff(c.DiffFileName)

	os.Exit(0)
}

func (c KillCmd) Run(cfg *args_handler.Config) {
	if !cfg.Kill {
		return
	}

	if !cfg.Confirm {
		fmt.Println("User confirmation required. Use --confirm to proceed.")
		os.Exit(1)
	}

	if !filepath.IsAbs(cfg.LockFile) {
		absPath, err := filepath.Abs(cfg.LockFile)
		if err != nil {
			fmt.Println("Invalid lock file path")
			os.Exit(1)
		}
		cfg.LockFile = absPath
	}

	fmt.Println("Lock file removed, background job will stop gracefully.")

	os.Exit(0)
}
