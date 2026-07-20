package os_manager

import (
	"os"
	"path/filepath"
	"testing"
)

func TestIsInPATH_Known(t *testing.T) {
	found, err := IsInPATH("sh")
	if err != nil {
		t.Fatal("unexpected error:", err)
	}
	if !found {
		t.Error("expected 'sh' to be in PATH")
	}
}

func TestIsInPATH_Unknown(t *testing.T) {
	found, err := IsInPATH("this-command-should-not-exist-xyzzy")
	if err == nil {
		t.Error("expected error for unknown command, got nil")
	}
	if found {
		t.Error("expected 'this-command-should-not-exist-xyzzy' NOT to be in PATH")
	}
}

func TestIsInPATH_Empty(t *testing.T) {
	found, err := IsInPATH("")
	if err == nil {
		t.Error("expected error for empty command, got nil")
	}
	if found {
		t.Error("expected empty command NOT to be in PATH")
	}
}

func TestIsInPATH_Ls(t *testing.T) {
	found, err := IsInPATH("ls")
	if err != nil {
		t.Fatal("unexpected error:", err)
	}
	if !found {
		t.Error("expected 'ls' to be in PATH")
	}
}

func TestGetAbsPath(t *testing.T) {
	abs := GetAbsPath("somefile.txt")
	if !filepath.IsAbs(abs) {
		t.Errorf("expected absolute path, got %q", abs)
	}
}

func TestChangeDir_Valid(t *testing.T) {
	orig, _ := os.Getwd()
	tmp := t.TempDir()
	ChangeDir(tmp)
	cwd, _ := os.Getwd()
	if cwd != tmp {
		t.Errorf("expected cwd %q, got %q", tmp, cwd)
	}
	os.Chdir(orig)
}
