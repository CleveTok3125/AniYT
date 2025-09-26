package common

type GenerateCompare interface {
	GenerateCompareList() error
	GetCompareList() [][]VideoInfo
}

type VideoInfo struct {
	Title string
	URL   string
}

type PlaylistURL struct {
	PlaylistURLs []string
}

type ComparingData struct {
	CompareListLocal    [][]VideoInfo
	ComparingListRemote [][]VideoInfo
}

type GlobalDiff struct {
	OnlyInLocal  []VideoInfo
	OnlyInRemote []VideoInfo
	TitleChanged []TitleChange
}

type TitleChange struct {
	URL      string
	OldTitle string
	NewTitle string
}

type DiffSummary struct {
	TotalChanges int
	OnlyInLocal  int
	OnlyInRemote int
	TitleChanged int
}
