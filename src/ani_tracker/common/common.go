package common

type GenerateCompare interface {
	GenerateCompareList()
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
