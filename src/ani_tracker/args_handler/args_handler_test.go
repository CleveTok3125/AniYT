package args_handler

import (
	"testing"
	"time"
)

func TestConfigDefaults(t *testing.T) {
	cfg := &Config{}
	if cfg.WorkingDir != "" {
		t.Errorf("expected empty WorkingDir, got %q", cfg.WorkingDir)
	}
	if cfg.Interval != 0 {
		t.Errorf("expected 0 Interval, got %v", cfg.Interval)
	}
	if cfg.Attempt != 0 {
		t.Errorf("expected 0 Attempt, got %d", cfg.Attempt)
	}
}

func TestConfigCustomValues(t *testing.T) {
	cfg := &Config{
		WorkingDir:        "/tmp/test",
		Confirm:           true,
		Kill:              true,
		NoDaemon:          true,
		Silent:            true,
		Interval:          30 * time.Minute,
		Attempt:           5,
		BackoffMultiplier: 2 * time.Second,
		UseBookmarksOnly:  true,
		ShowDiff:          true,
		LogFile:           "custom.log",
		LockFile:          "custom.lock",
	}
	if cfg.WorkingDir != "/tmp/test" {
		t.Errorf("expected WorkingDir '/tmp/test', got %q", cfg.WorkingDir)
	}
	if !cfg.Confirm {
		t.Error("expected Confirm to be true")
	}
	if !cfg.Kill {
		t.Error("expected Kill to be true")
	}
	if !cfg.Silent {
		t.Error("expected Silent to be true")
	}
	if cfg.Interval != 30*time.Minute {
		t.Errorf("expected Interval 30m, got %v", cfg.Interval)
	}
	if cfg.Attempt != 5 {
		t.Errorf("expected Attempt 5, got %d", cfg.Attempt)
	}
	if cfg.BackoffMultiplier != 2*time.Second {
		t.Errorf("expected BackoffMultiplier 2s, got %v", cfg.BackoffMultiplier)
	}
	if !cfg.UseBookmarksOnly {
		t.Error("expected UseBookmarksOnly to be true")
	}
	if !cfg.ShowDiff {
		t.Error("expected ShowDiff to be true")
	}
	if cfg.LogFile != "custom.log" {
		t.Errorf("expected LogFile 'custom.log', got %q", cfg.LogFile)
	}
	if cfg.LockFile != "custom.lock" {
		t.Errorf("expected LockFile 'custom.lock', got %q", cfg.LockFile)
	}
}

func TestGlobalCfgNotNil(t *testing.T) {
	if Cfg == nil {
		t.Fatal("expected global Cfg to be initialized")
	}
}
