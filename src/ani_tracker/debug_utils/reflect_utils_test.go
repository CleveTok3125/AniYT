package debug_utils

import (
	"testing"
)

type testStruct struct {
	Name  string
	Value int
}

type testNested struct {
	Inner testStruct
	Label string
}

func TestGetField(t *testing.T) {
	obj := testStruct{Name: "hello", Value: 42}

	name := GetField(obj, "Name")
	if name != "hello" {
		t.Errorf("expected 'hello', got %v", name)
	}

	value := GetField(obj, "Value")
	if value != 42 {
		t.Errorf("expected 42, got %v", value)
	}
}

func TestGetField_Pointer(t *testing.T) {
	obj := &testStruct{Name: "pointer", Value: 99}

	name := GetField(obj, "Name")
	if name != "pointer" {
		t.Errorf("expected 'pointer', got %v", name)
	}

	value := GetField(obj, "Value")
	if value != 99 {
		t.Errorf("expected 99, got %v", value)
	}
}

func TestGetField_Nested(t *testing.T) {
	obj := testNested{Inner: testStruct{Name: "inner", Value: 7}, Label: "outer"}

	label := GetField(obj, "Label")
	if label != "outer" {
		t.Errorf("expected 'outer', got %v", label)
	}

	inner := GetField(obj, "Inner")
	if _, ok := inner.(testStruct); !ok {
		t.Errorf("expected Inner to be testStruct, got %T", inner)
	}
}
