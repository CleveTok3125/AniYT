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
	err := os.Remove(lf.FilePath)
	switch {
	case err == nil:
		log.Printf("%s removed successfully", lf.FilePath)
	case os.IsNotExist(err):
		log.Printf("Lock file %s already removed", lf.FilePath)
	default:
		log.Println("Unable to remove lock file:", err)
	}
}
