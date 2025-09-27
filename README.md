# AniYT

[![License](https://img.shields.io/github/license/CleveTok3125/AniYT)](https://github.com/CleveTok3125/AniYT/blob/main/LICENSE)
[![Release](https://img.shields.io/github/v/release/CleveTok3125/AniYT)](https://github.com/CleveTok3125/AniYT/releases)
[![CodeQL](https://github.com/CleveTok3125/AniYT/workflows/CodeQL/badge.svg)](https://github.com/CleveTok3125/AniYT/security/code-scanning)
[![CI](https://github.com/CleveTok3125/AniYT/actions/workflows/ci.yml/badge.svg)](https://github.com/CleveTok3125/AniYT/actions/workflows/ci.yml)
[![Build](https://github.com/CleveTok3125/AniYT/actions/workflows/build.yml/badge.svg)](https://github.com/CleveTok3125/AniYT/actions/workflows/build.yml)

A feauture rich cli tool to browse and watch videos in YouTube playlists. Specially designed for watching anime on YouTube.

# Demo
```
$ /path/to/project/AniYT/ani_yt -c MuseAsia -l

(O) Hide all options
(N) Next page
(P) Previous page
(P:<integer>) Jump to page
(J) Jump to next unviewed
(U) Toggle link
(B) Toggle bookmark
(B:<integer>) Add/remove bookmark
(T:<integer>) View thumbnail
(I:<integer>) number of items per page
(Q) Quit

Page: 2/34 (24/401)

(13) (Full Series) I've Been Killing Slimes for 300 Years and Maxed Out My Level [English Sub]
(14) I'm the Evil Lord of an Intergalactic Empire! [English Sub]
(15) Lord of Vermilion: The Crimson King [English Sub]
(16) (Full Series) Is the Order a Rabbit? [English Sub]
(17) Crayon Shinchan movies [English Sub]
(18) Just Because! [English Sub]
(19) [English Dub] Frieren: Beyond Journey's End
(20) Cells at Work! [English Sub]
(21) BanG Dream! Ave Mujica [English Sub]
(22) MOMENTARY LILY [English Sub]
(23) Even Given the Worthless "Appraiser" Class, I'm Actually the Strongest [English Sub]
(24) From Bureaucrat to Villainess: Dad's Been Reincarnated! [English Sub]

Select (13): 17
```

___
Command line interface ([v0.9.6](https://github.com/CleveTok3125/AniYT/releases/tag/v0.9.6))

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

10. **Playlist update notification**\
   Notify when there is a new video in the watched playlist.

To see the full features, see [cli_help.txt](https://github.com/CleveTok3125/AniYT/blob/artifacts/artifacts/help/cli_help.txt)

# Dependencies
- Python >= 3.9 (recommended >= 3.13)
- _Go >= 1.22 (recommended >= 1.25.1)_*
- MPV or MPV-X11
- YT-DLP

*Only needed when building from source

# Installation
## Install from Source (rolling)
```bash
pip install git+https://github.com/CleveTok3125/AniYT.git
```
## Install from GitHub Releases (recommended)
```bash
pip install --index-url https://clevetok3125.github.io/AniYT/ --extra-index-url https://pypi.org/simple aniyt
```

# Usage
## Use with Python Module
```bash
python -m ani-yt -h
python -m ani-yt tracker -h
```
## Use with CLI Directly
```bash
ani-yt -h
ani-tracker -h
```
## Example
```bash
ani-yt -c MuseAsia   # Update/Create new list of playlists from specified channel
ani-yt -l   # List all available playlists
ani-yt search "Attack on Titan"  # Search and return matching playlists
ani-tracker --working-dir "./data" --interval 1h   # Watch new videos every 1 hour based on data generated from `ani-yt`
```

# Uninstall
```bash
python -m pip uninstall AniYT
```

# Install and run locally
## Clone repo
```bash
git clone https://github.com/CleveTok3125/AniYT/
cd AniYT
```
## Setup environment
```bash
python -m venv venv
source venv/bin/activate
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
## Build Go binary
```bash
cd src/ani_tracker
go build -o ../../bin/ani-tracker .
cd ../../
```
## Build
```bash
pip install .
```
## Run live for debugging
### ani-yt 
```bash
PYTHONPATH=src python -m ani_yt.ani_yt -h
```
### ani-tracker
```bash
cd src/ani_tracker
go run . -d ./../../data --no-daemon -h
cd ../../
```

# About additional/generated files
- `./mpv-config/custom.conf`: like `mpv.conf`. Use if you want to separate it from the original MPV configuration.
- `./data/playlists.json`: stores playlist information.\
Mainly to reduce repeated calls to YT-DLP API which slows down retrieval significantly when the channel has many playlists.
- `./data/history.json`: store viewing history.
- `./data/bookmark.json`: store bookmark.
- `./data/channel_sources.txt`: list of channel sources.
- `./mpv-scripts/gestures.lua`: Recommended if running in graphical session via termux-x11. [Details](https://github.com/CleveTok3125/AniYT-mpv-gestures)
- `./mpv-scripts/sponsorblock_minimal.lua`: Use SponsorBlock to skip sponsorships. Similar to `gesture.lua`, it is only loaded automatically if in a graphical session via termux-x11.
- `./data/playlists.diff`: File containing difference information after running `ani-tracker`
- `./data/*.log`: Log files for debugging
- `./data/*.lock`: This is a file created when the program runs. Delete it to terminate the program.

*If using python modules, these files are automatically generated in the working directory. `custom.conf` is not automatically generated, however it can be manually created in the working directory to use it.*

# Additional options
## SponsorBlock
- Use SponsorBlock plugin for MPV to skip OP/EN

## Ani-Tracker: Notify new videos in playlist
- This feature is separated from the original project and named `ani-tracker`
- Instructions are included in `ani-yt --full-help`
- The binary is included in the wheel of the original project, and can be run directly on the CLI. See [Usage](#usage)
- Can be run via the `tracker` subcommand of `ani-yt` as a wrapper.\
   For example `ani-yt tracker --help` will print help for `ani-tracker`

## Android
- For Android, use MPV with youtube-dl built-in. Refer to [this link](https://github.com/mpv-android/mpv-android/pull/58)\
   In addition, you can use MPV on [Termux-x11](https://github.com/termux/termux-x11). Refer [this setup instructions](https://github.com/termux/termux-x11?tab=readme-ov-file#Setup-instructions).
- In `--mpv-player termux-x11` mode, `gestures.lua` script will be loaded by default if present to provide mouse/touch gestures. See [setup instructions](https://github.com/CleveTok3125/AniYT-mpv-gestures?tab=readme-ov-file#setup-instructions) for usage. This mode will select monitor 1 by default and send the mpv run command through it instead of having to use the command line in the graphical session. **Requires `mpv-x`**\
   Need to run termux-x11 in the background in a separate termux session. If using `xfce4`, use (one of) [these commands](https://github.com/termux/termux-x11?tab=readme-ov-file#running-graphical-applications) to launch
   ```bash
   termux-x11 :1 -xstartup "dbus-launch --exit-with-session xfce4-session"
   ```
   
# Non-project-related notification
_This notification is for the anime fan community, not related to this project._

Currently, channels that provide free high-quality copyrighted anime on YouTube such as MuseAsia are removing some old anime and moving them to other platforms (usually paid platforms). You can refer to alternative solutions such as [ani-cli](https://github.com/pystardust/ani-cli) or [AnimeVsub](https://github.com/anime-vsub) for Vietsub (no dub yet).
