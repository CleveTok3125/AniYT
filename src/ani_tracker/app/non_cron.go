package app

import (
	"ani-tracker/args_handler"
	"ani-tracker/comparer"
	"os"
)

type NonCrons interface {
	Run(cfg *args_handler.Config)
}

type ShowDiffCmd struct {
	DiffFileName string
}

func (c ShowDiffCmd) Run(cfg *args_handler.Config) {
	if !cfg.ShowDiff {
		return
	}

	comparer.ShowDiff(c.DiffFileName)

	os.Exit(0)
}
