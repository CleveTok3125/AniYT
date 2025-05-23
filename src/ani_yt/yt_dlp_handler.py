from urllib.parse import urljoin, urlparse
import os
import subprocess

import ujson as json
import yt_dlp

# Custom lib
from os_manager import OSManager
from exceptions import MissingChannelUrl


class YT_DLP_Options:
    def __init__(self, quiet=True, no_warnings=True):
        self.ydl_opts = {
            "extract_flat": True,
            "force_generic_extractor": False,
            "quiet": quiet,
            "no_warnings": no_warnings,
        }


class YT_DLP:
    def __init__(self, channel_url, ydl_options: YT_DLP_Options):
        self.channel_url = channel_url

        if self.channel_url:
            if not (
                bool((parsed_url := urlparse(self.channel_url)).scheme)
                and bool(parsed_url.netloc)
            ):
                if self.channel_url[:2] == "UC":
                    self.channel_url = urljoin(
                        "https://www.youtube.com/channel/", self.channel_url
                    )
                else:
                    self.channel_url = urljoin(
                        "https://www.youtube.com/", self.channel_url
                    )
            self.channel_url = urljoin(
                self.channel_url
                if self.channel_url.endswith("/")
                else self.channel_url + "/",
                "playlists",
            )
        self.ydl_options = ydl_options

    def get_playlist(self):
        try:
            if not self.channel_url:
                raise MissingChannelUrl("No channel url specified.")

            with yt_dlp.YoutubeDL(self.ydl_options.ydl_opts) as ydl:
                result = ydl.extract_info(self.channel_url, download=False)
            return result
        except yt_dlp.utils.DownloadError:
            OSManager.exit(404)

    @staticmethod
    def standalone_get_video(url, opts):
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            return info
        except yt_dlp.utils.DownloadError:
            OSManager.exit(404)

    def get_video(self, url):
        return YT_DLP.standalone_get_video(url, self.ydl_options.ydl_opts)

    @staticmethod
    def standalone_get_thumbnail(url, opts):
        info = YT_DLP.standalone_get_video(url, opts)
        return info["thumbnails"][-1]["url"]

    def get_stream(self, url):
        formats = self.get_video(url)
        return (
            formats["requested_formats"][0]["url"],
            formats["requested_formats"][1]["url"],
        )

    @staticmethod
    def download(url, cats="all", extra_args=[], args=None, capture_output=False):
        if args is None:
            args = [
                "--no-warnings",
                "--progress",
                "--sponsorblock-remove",
                cats,
                url,
                "--output",
                os.path.join(os.getcwd(), "%(title)s [%(id)s].%(ext)s"),
                "--print",
                "after_move:filepath",
            ]

        if extra_args:
            if isinstance(extra_args, str):
                args.append(extra_args)
            else:
                args += extra_args

        command = ["yt-dlp"] + args
        result = subprocess.run(command, capture_output=capture_output)
        return result.stdout
