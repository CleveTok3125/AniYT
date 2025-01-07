# AniYT
A cli tool to browse and watch videos in YouTube playlists. Specially designed for watching anime on YouTube.

```
$ /path/to/project/AniYT/ani-yt -c MuseAsia -l

(N) Next page
(P) Previous page
(U) Show link
(P:integer) Jump to the specified page.
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