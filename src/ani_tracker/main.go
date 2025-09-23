// Main logic
package main

import (
	"ani-tracker/common"
	"ani-tracker/comparer"
	"ani-tracker/history_handler"
	"ani-tracker/yt_dlp_handler"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"
)

const lockFile = "ani-tracker.lock"
const logFile = "ani-tracker.log"
const logging = false
const INTERVAL = 3600

var logFileHandle *os.File

func main() {
	changeDir()

	if logging {
		setupLogging()
		defer finishLogging()
	}

	createPIDfile()
	defer clean()

	catchTerminateSignal()

	cronJob(conductor)
}

func setupLogging() {
	var err error
	logFileHandle, err = os.OpenFile(logFile, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		log.Fatal(err)
	}

	log.SetOutput(logFileHandle)
}

func finishLogging() {
	if err := logFileHandle.Close(); err != nil {
		log.Printf("Failed to close file: %v", err)
	}
}

func changeDir() {
	err := os.Chdir("../../data")
	if err != nil {
		log.Fatal("Failed to change dir: ", err)
	}
}

func createPIDfile() {
	file, err := os.Create(lockFile)
	if err != nil {
		log.Printf("Program is running or can not create %s: %v", lockFile, err)
		return
	}
	if err := file.Close(); err != nil {
		log.Printf("Failed to close file: %v", err)
	}
}

func catchTerminateSignal() {
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigs
		log.Println("Terminate signal received, cleaning up...")
		clean()
		os.Exit(0)
	}()
}

func clean() {
	if err := os.Remove(lockFile); err != nil {
		log.Fatal("Unable to stop properly: ", err)
	}

	log.Printf("%s removed successfully", lockFile)
}

func cronJob(job func()) {
	log.Println("Program is running in background")

	for {
		if _, err := os.Stat(lockFile); os.IsNotExist(err) {
			log.Println("Stop signal received, exiting...")
			return
		}

		log.Println("Running...")

		job()

		log.Printf("Waiting for the next run: %s", time.Now().Add(INTERVAL*time.Second).Format("2006/01/02 15:04:05"))
		time.Sleep(INTERVAL * time.Second)
	}
}

func conductor() {
	historyHandler := &history_handler.HistoryFile{FileName: "history.json"}
	ytdlpHandler := &yt_dlp_handler.PlaylistHandler{HistoryHandler: historyHandler}
	cmp := &comparer.DiffFile{FileName: "playlists.diff"}

	handlers := []common.GenerateCompare{
		historyHandler,
		ytdlpHandler,
	}

	for _, handler := range handlers {
		handler.GenerateCompareList()
		// debug_utils.PrettyDump(handler.GetCompareList(), "    ")
	}

	cmp.Diff(historyHandler.GetCompareList(), ytdlpHandler.GetCompareList())
}
