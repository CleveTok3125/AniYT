package args_handler

import (
	"github.com/alecthomas/kong"
)

func Listener() {
	kong.Parse(Cfg, kong.Description("ani-tracker CLI"), kong.UsageOnError())
}
