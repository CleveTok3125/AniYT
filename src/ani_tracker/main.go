// Main logic
package main

import (
	"ani-tracker/app"
	"ani-tracker/args_handler"
	"ani-tracker/debug_utils"
	"ani-tracker/os_manager"
	"fmt"
	"os"
)

const HistoryFileName = "history.json"
const BookmarkFileName = "bookmark.json"
const DiffFileName = "playlists.diff"

var logFileHandle *os.File

func main() {
	args_handler.Listener()
	cfg := args_handler.Cfg

	os_manager.ChangeDir(cfg.WorkingDir)

	nonCrons := []app.NonCrons{
		app.ShowDiffCmd{DiffFileName: DiffFileName},
	}
	for _, cmd := range nonCrons {
		cmd.Run(cfg)
	}

	if !cfg.NoDaemon {
		logInst := debug_utils.LogFile{FilePath: cfg.LogFile, LogFileHandle: logFileHandle}
		fmt.Printf("Start logging at: \"%s\"\n", os_manager.GetAbsPath(cfg.LogFile))
		logInst.SetupLogging()
		defer logInst.FinishLogging()
	}

	lock := &os_manager.LockFile{FilePath: cfg.LockFile}
	lock.CreateLockFile()
	defer lock.RemoveLockFile()

	stop := make(chan struct{})
	os_manager.CatchTerminateSignal(stop)

	appInstance := &app.Config{
		HistoryFileName:  HistoryFileName,
		BookmarkFileName: BookmarkFileName,
		DiffFileName:     DiffFileName,
		UseBookmarksOnly: cfg.UseBookmarksOnly,
		Silent:           cfg.Silent,
	}

	cron := app.CronJob{
		Interval:          cfg.Interval,
		Job:               func() error { return appInstance.Conductor() },
		Attempt:           cfg.Attempt,
		BackoffMultiplier: cfg.BackoffMultiplier,
		Stop:              stop,
		LockFile:          lock,
	}

	cron.Run()
}
