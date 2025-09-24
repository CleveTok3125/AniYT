// Main logic
package main

import (
	"ani-tracker/app"
	"ani-tracker/args_handler"
	"ani-tracker/debug_utils"
	"ani-tracker/os_manager"
	"fmt"
	"log"
	"os"
)

var logFileHandle *os.File

func main() {
	args_handler.Listener()
	cfg := args_handler.Cfg

	os_manager.ChangeDir(cfg.WorkingDir)

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

	cron := app.CronJob{
		Interval: cfg.Interval,
		Job:      app.Conductor,
		Stop:     stop,
		LockFile: lock,
	}
	err := cron.Run()
	if err != nil {
		log.Println("Cronjob stops with error: ", err)
	}
}
