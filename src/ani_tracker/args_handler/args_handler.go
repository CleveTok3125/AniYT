package args_handler

import (
	"time"

	"github.com/alecthomas/kong"
)

type Config struct {
	WorkingDir string `short:"d" required:"true" help:"Working directory"`

	NoDaemon          bool          `default:"false" help:"Do not daemonize"`
	Silent            bool          `short:"s" default:"false" help:"Run in silent mode (for automation)"`
	Interval          time.Duration `short:"i" default:"1h" help:"Interval duration"`
	Attempt           int           `default:"3" help:"Number of retries before exiting completely"`
	BackoffMultiplier time.Duration `default:"1s" help:"Retry time of cronjobs = Attempt * BackoffMultiplier"`

	UseBookmarksOnly bool `name:"marked" short:"m" default:"false" help:"Only track marked playlists in history"`

	ShowDiff bool   `name:"diff" default:"false" help:"View contents of exported diff file"`
	LogFile  string `default:"ani-tracker.log" help:"Log file path"`
	LockFile string `default:"ani-tracker.lock" help:"Lock file path"`
}

var Cfg = &Config{}

func Listener() {
	kong.Parse(Cfg, kong.Description("ani-tracker CLI"), kong.UsageOnError())
}
