// Main logic
package main

import (
	"ani-tracker/debug_utils"
	"ani-tracker/os_manager"
	"log"
	"os"
	"time"
)

const lockFile = "ani-tracker.lock"
const logFile = "ani-tracker.log"
const logging = false
const INTERVAL = 1 * time.Second

var logFileHandle *os.File

func main() {
	os_manager.ChangeDir("../../data")

	if logging {
		logInst := debug_utils.LogFile{FilePath: logFile, LogFileHandle: logFileHandle}

		logInst.SetupLogging()
		defer logInst.FinishLogging()
	}

	osMngr := os_manager.LockFile{FilePath: lockFile}
	osMngr.CreateLockFile()
	defer osMngr.RemoveLockFile()

	stop := make(chan struct{})
	os_manager.CatchTerminateSignal(stop)

	err := cronJob(INTERVAL, conductor, stop)
	if err != nil {
		log.Println("Cronjob stops with error: ", err)
	}
}
