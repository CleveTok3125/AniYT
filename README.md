# AniYT
A cli tool to browse and watch videos in YouTube playlists. Specially designed for watching anime on YouTube.

# Demo
```
$ /path/to/project/AniYT/ani-yt -c MuseAsia -l

(N) Next page
(P) Previous page
(P:integer) Jump to the specified page
(U) Toggle link
(B) Toggle bookmark
(B:integer) Add/remove specified item to bookmark
(Q) Quit

Page: 1/35 (12/417)

(1) Cells at Work! [English Sub]
(2) BanG Dream! Ave Mujica [English Sub]
(3) MOMENTARY LILY [English Sub]
(4) I Want to Escape from Princess Lessons [English Sub]
(5) Beheneko: The Elf-Girl’s Cat is Secretly an S-Ranked Monster! [English Sub]
(6) (Limited time only) Attack on Titan [English Sub]
(7) HAIGAKURA [English Sub]
(8) (Full Series) Re:ZERO -Starting Life in Another World- [English Sub]
(9) Re:ZERO -Starting Life in Another World- Season 3 [English Sub]
(10) The Most Notorious “Talker” Runs the World’s Greatest Clan [English Sub]
(11) Let This Grieving Soul Retire [English Sub]
(12) Aniplex Online Fest 2024

Select: 1
```

![Demo](./demo.png)

# Key Features

1. **Update Playlist from YouTube Channel**  
   Update playlists from a YouTube channel using its URL, ID, or Handle.

2. **Browse Playlists and Videos**  
   Browse through playlists and videos in the saved playlists with pagination for easier navigation.

3. **Search Playlists**  
   Search for playlists by keyword.

4. **History Tracking**  
   Continue watching previously viewed videos through the watch history and history tracking.

5. **Bookmarking**
   Bookmark favorite videos or playlists.

6. **Play Videos with MPV**  
   Play videos using the MPV player (supports both Android and auto modes).

7. **Download Videos with SponsorBlock**  
   Download videos and automatically skip sponsors using SponsorBlock.

# Installation
```bash
git clone https://github.com/CleveTok3125/AniYT/
cd AniYT
pip install -r requirements.txt
```
# Usage
```bash
python ani-yt.py -h
```

# About additional/generated files
- `custom.conf`: like `mpv.conf`. Use if you want to separate it from the original MPV configuration
- `playlists.json`: stores playlist information.\
Mainly to reduce repeated calls to YT-DLP API which slows down retrieval significantly when the channel has many playlists.
- `history.json`: store viewing history.
- `bookmark.json`: store bookmark

# Additional options
- Use SponsorBlock plugin for MPV to skip OP/EN
- For Android, use MPV with youtube-dl built-in. Refer to [this link](https://github.com/mpv-android/mpv-android/pull/58)