package debug_utils

import "github.com/davecgh/go-spew/spew"

func PrettyDump(data any, indent_args ...string) {
	indent := "  "
	if len(indent_args) > 0 {
		indent = indent_args[0]
	}
	config := spew.ConfigState{Indent: indent}
	config.Dump(data)
}
