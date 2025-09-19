package json_utils

import (
	"bytes"
	"encoding/json"
	"github.com/tidwall/gjson"
	"io"
	"log"
	"os"
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

func DumpJsonStr(all []any, outputFile string) {
	file, err := os.Create(outputFile)
	if err != nil {
		log.Fatalf("Cannot create file: %v", err)
	}
	defer file.Close()

	enc := json.NewEncoder(file)
	enc.SetIndent("", "    ")
	if err := enc.Encode(all); err != nil {
		log.Fatalf("Failed to write JSON: %v", err)
	}

	log.Printf("JSON dumped successfully to %s", outputFile)
}
