package os_manager

import (
	"log"
	"os"
	"os/exec"
	"path/filepath"
)

func IsInPATH(path string) (bool, error) {
	_, err := exec.LookPath(path)

	if err == nil {
		return true, err
	}

	return false, err
}

func GetAbsPath(fileName string) string {
	absPath, err := filepath.Abs(fileName)
	if err != nil {
		log.Fatal("Error: ", err)
	}
	return absPath
}

func ChangeDir(dir string) {
	err := os.Chdir(dir)
	if err != nil {
		log.Fatal("Failed to change dir: ", err)
	}
}
