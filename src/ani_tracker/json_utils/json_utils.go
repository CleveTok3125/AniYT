package json_utils

import (
	"encoding/json"
	"strings"

	"github.com/tidwall/gjson"
)

func GetStringArray(jsonStr string, path string) []string {
	results := []string{}
	values := gjson.Get(jsonStr, path).Array()
	for _, v := range values {
		results = append(results, v.String())
	}
	return results
}

func ParseMultipleJSON(jsonStr string) ([]any, error) {
	lines := strings.Split(jsonStr, "\n")
	var all []any

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || line[0] != '{' {
			continue
		}

		var obj any
		if err := json.Unmarshal([]byte(line), &obj); err != nil {
			return nil, err
		}
		all = append(all, obj)
	}

	return all, nil
}
