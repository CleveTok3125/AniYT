package debug_utils

import (
	"log"
	"reflect"
)

func GetField(obj any, fieldName string) any {
	refl := reflect.ValueOf(obj)
	if refl.Kind() == reflect.Pointer {
		refl = refl.Elem()
	}

	field := refl.FieldByName(fieldName)
	if !field.IsValid() {
		log.Fatal("Warning: Field not found:", fieldName)
	}

	return field.Interface()
}
