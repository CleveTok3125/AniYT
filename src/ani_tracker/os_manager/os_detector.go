package os_manager

import (
	"os"
	"os/exec"
	"strings"
)

// IsAndroid Check if the device is running Android (Termux), usually to call the corresponding support APIs
func IsAndroid() bool {
	prefix := os.Getenv("PREFIX")
	if strings.Contains(prefix, "com.termux") {
		return true
	}

	out, err := exec.Command("uname", "-a").Output()
	if err != nil {
		return false
	}

	uname := strings.ToLower(string(out))
	return strings.Contains(uname, "android")
}
