package args_handler

import "time"

type Config struct {
	NoDaemon   bool          `default:"false" help:"Do not daemonize"`
	LogFile    string        `default:"ani-tracker.log" help:"Log file path"`
	LockFile   string        `default:"ani-tracker.lock" help:"Lock file path"`
	Interval   time.Duration `short:"i" default:"1h" help:"Interval duration"`
	WorkingDir string        `short:"d" required:"true" help:"Working directory"`
}

var Cfg = &Config{}
