package debug_utils

import (
	"log"
	"os"
)

type LogFile struct {
	FilePath      string
	LogFileHandle *os.File
}

func (lf *LogFile) SetupLogging() {
	var err error
	lf.LogFileHandle, err = os.OpenFile(lf.FilePath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		log.Fatal(err)
	}

	log.SetOutput(lf.LogFileHandle)
}

func (lf *LogFile) FinishLogging() {
	if err := lf.LogFileHandle.Close(); err != nil {
		log.Printf("Failed to close file: %v", err)
	}
}
