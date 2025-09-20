package common

type VideoInfo struct {
	Title string
	URL   string
}

type PlaylistURL struct {
	PlaylistURLs []string
}

type Comparing struct {
	CompareListLocal    [][]VideoInfo
	ComparingListRemote [][]VideoInfo
}
