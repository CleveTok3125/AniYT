package json_utils

import (
	"bytes"
	"encoding/json"
	"io"

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
	dec := json.NewDecoder(bytes.NewReader([]byte(jsonStr)))
	var all []any

	for {
		var obj any
		if err := dec.Decode(&obj); err != nil {
			if err == io.EOF {
				break
			}
			return nil, err

		}
		all = append(all, obj)
	}

	return all, nil
}
