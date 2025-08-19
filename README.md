# AniYT
A feauture rich cli tool to browse and watch videos in YouTube playlists. Specially designed for watching anime on YouTube.

# Demo
```
$ /path/to/project/AniYT/ani_yt -c MuseAsia -l

(N) Next page
(P) Previous page
(P:<integer>) Jump to page
(O) Hide all options
(U) Toggle link
(B) Toggle bookmark
(B:<integer>) Add/remove bookmark
(T:<integer>) View thumbnail
(I:<integer>) number of items per page
(Q) Quit

Page: 2/35 (24/420)

(13) MOMENTARY LILY [English Sub]
(14) Even Given the Worthless "Appraiser" Class, I'm Actually the Strongest [English Sub]
(15) From Bureaucrat to Villainess: Dad's Been Reincarnated! [English Sub]
(16) I Want to Escape from Princess Lessons [English Sub]
(17) I Left my A-Rank Party to Help My Former Students Reach the Dungeon Depths! [English Sub]
(18) Beheneko: The Elf-Girl’s Cat is Secretly an S-Ranked Monster! [English Sub]
(19) (Limited time only) Attack on Titan [English Sub]
(20) HAIGAKURA [English Sub]
(21) (Full Series) Re:ZERO -Starting Life in Another World- [English Sub]
(22) Re:ZERO -Starting Life in Another World- Season 3 [English Sub]
(23) The Most Notorious “Talker” Runs the World’s Greatest Clan [English Sub]
(24) Let This Grieving Soul Retire [English Sub]

Select: 13
```

___
Command line interface (old version)

![Demo](./demo.png)

# Key Features

1. **Update Playlist from YouTube Channel**\
   Update playlists from a YouTube channel using its URL, ID, or Handle. Support updating and combining playlists from multiple sources, similar to package manager.

2. **Browse Playlists and Videos**\
   Browse through playlists and videos in the saved playlists with pagination for easier navigation.

3. **Search Playlists**\
   Search for playlists by keyword.

4. **History Tracking**\
   Continue watching previously viewed videos through the watch history and history tracking.

5. **Bookmarking**\
   Bookmark favorite videos or playlists.

6. **Play Videos with MPV**\
   Play videos using the MPV player (supports both Android and auto modes).

7. **View Thumbnail**\
   View thumbnails with MPV player

8. **Download Videos with SponsorBlock**\
   Download videos and automatically skip sponsors using SponsorBlock.

9. **Automatically check for yt-dlp updates**\
   Only check Python dependency, MPV Player if not using this dependency needs to be updated manually.

# Installation
## Install from Source
```bash
git clone https://github.com/CleveTok3125/AniYT/
cd AniYT
pip install .
```
## Install from Remote
```bash
pip install git+https://github.com/CleveTok3125/AniYT.git
```

# Usage
## Use with Python Module
```bash
python -m ani-yt -h
```
## Use with CLI Directly
```bash
ani-yt -h
```
## Example
```bash
ani-yt -c MuseAsia   # Update/Create new list of playlists from specified channel
ani-yt -l   # List all available playlists
ani-yt search "Attack on Titan"  # Search and return matching playlists
```

# Uninstall
```bash
python -m pip uninstall AniYT
```

# Run from source
## Clone repo
```bash
git clone https://github.com/CleveTok3125/AniYT/
cd AniYT
```
## Install requirements
```bash
pip install -r requirements.txt
pip install setuptools cython
```
## Compile Cython
```bash
python setup.py build_ext --inplace
```
## Run
```bash
PYTHONPATH=src python -m ani_yt.ani_yt -h
```

# About additional/generated files
- `custom.conf`: like `mpv.conf`. Use if you want to separate it from the original MPV configuration.
- `playlists.json`: stores playlist information.\
Mainly to reduce repeated calls to YT-DLP API which slows down retrieval significantly when the channel has many playlists.
- `history.json`: store viewing history.
- `bookmark.json`: store bookmark.
- `channel_sources.txt`: list of channel sources.

*If using python modules, these files are automatically generated in the working directory. `custom.conf` is not automatically generated, however it can be manually created in the working directory to use it.*

# Additional options
- Use SponsorBlock plugin for MPV to skip OP/EN
- For Android, use MPV with youtube-dl built-in. Refer to [this link](https://github.com/mpv-android/mpv-android/pull/58)\
   In addition, you can use MPV on [Termux-x11](https://github.com/termux/termux-x11) with DE `XFCE4` by default. Refer [this setup instructions](https://github.com/termux/termux-x11?tab=readme-ov-file#Setup-instructions).

# Non-project-related notification
_This notification is for the anime fan community, not related to this project._

Currently, channels that provide free high-quality copyrighted anime on YouTube such as MuseAsia are removing some old anime and moving them to other platforms (usually paid platforms). You can refer to alternative solutions such as [ani-cli](https://github.com/pystardust/ani-cli) or [AnimeVsub](https://github.com/anime-vsub) for Vietsub (no dub yet).
