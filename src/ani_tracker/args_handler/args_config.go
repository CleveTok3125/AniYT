package args_handler

import "time"

type Config struct {
	WorkingDir string `short:"d" required:"true" help:"Working directory"`

	NoDaemon          bool          `default:"false" help:"Do not daemonize"`
	Interval          time.Duration `short:"i" default:"1h" help:"Interval duration"`
	Attempt           int           `default:"3" help:"Number of retries before exiting completely"`
	BackoffMultiplier time.Duration `default:"1s" help:"Retry time of cronjobs = Attempt * BackoffMultiplier"`

	UseBookmarksOnly bool `name:"marked" short:"m" default:"false" help:"Only track marked playlists in history"`

	LogFile  string `default:"ani-tracker.log" help:"Log file path"`
	LockFile string `default:"ani-tracker.lock" help:"Lock file path"`
}

var Cfg = &Config{}
