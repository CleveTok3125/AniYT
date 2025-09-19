package json_utils

import (
	"bytes"
	"encoding/json"
	"io"
	"log"

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

func GetBytesStringArray(jsonAny []any, path string) []string {
	jsonObj, err := json.Marshal(jsonAny)
	if err != nil {
		log.Fatalf("Failed to marshal JSON: %v", err)
	}

	results := []string{}
	values := gjson.GetBytes(jsonObj, path).Array()
	for _, v := range values {
		results = append(results, v.String())
	}
	return results
}

func ParseMultipleJSON(jsonStr string) []any {
	dec := json.NewDecoder(bytes.NewReader([]byte(jsonStr)))
	var all []any

	for {
		var obj any
		if err := dec.Decode(&obj); err != nil {
			if err == io.EOF {
				break
			}
			log.Fatalf("Failed to parse JSON: %v", err)
		}
		all = append(all, obj)
	}

	return all
}

func GetJSONValueAt(jsonStr string, key string, index int) any {
	var arr []map[string]any
	if err := json.Unmarshal([]byte(jsonStr), &arr); err != nil {
		log.Fatalf("Parse error: %v", err)
	}

	if index >= 0 {
		if index >= len(arr) {
			log.Fatalf("Index %d out of range", index)
		}
		return arr[index][key] // value (need type assertion)
	}

	values := []any{}
	for _, obj := range arr {
		if v, ok := obj[key]; ok {
			values = append(values, v)
		}
	}
	return values // slice
}

func GetJSONValue(jsonStr string, key string) []any {
	return GetJSONValueAt(jsonStr, key, -1).([]any)
}

func GetJSONValueCount(jsonStr string, key string) int {
	var arr []map[string]any
	if err := json.Unmarshal([]byte(jsonStr), &arr); err != nil {
		log.Fatalf("Parse error: %v", err)
	}

	count := 0
	for _, obj := range arr {
		if _, ok := obj[key]; ok {
			count++
		}
	}
	return count
}
