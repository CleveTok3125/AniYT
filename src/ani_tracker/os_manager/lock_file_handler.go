package os_manager

import (
	"log"
	"os"
)

type LockFile struct {
	FilePath string
}

func (lf *LockFile) CreateLockFile() {
	file, err := os.Create(lf.FilePath)
	if err != nil {
		log.Printf("Program is running or can not create %s: %v", lf.FilePath, err)
		return
	}
	if err := file.Close(); err != nil {
		log.Printf("Failed to close file: %v", err)
	}
}

func (lf *LockFile) RemoveLockFile() {
	if err := os.Remove(lf.FilePath); err != nil {
		log.Fatal("Unable to stop properly: ", err)
	}

	log.Printf("%s removed successfully", lf.FilePath)
}
