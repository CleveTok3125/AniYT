from urllib.parse import urljoin, urlparse
import json
import subprocess
import os
import sys
import argparse
from itertools import zip_longest

import yt_dlp

class MissingChannelUrl(Exception):
	pass

class OSManager:
	@staticmethod
	def exit(n=0):
		os._exit(n)

	@staticmethod
	def exists(path):
		if os.path.exists(path):
			return True
		return False

	@staticmethod
	def delete_file(path):
		if os.path.exists(path):
			try:
				os.remove(path)
			except Exception as e:
				print(e)

	@staticmethod
	def android_check():
		return True if os.name == 'posix' and 'android' in os.uname().release.lower() else False

class DataProcessing:
	@staticmethod
	def omit(data):
		result = []
		for entry in data.get('entries', []):
			if entry.get('_type', '') == 'url':
				result.append((entry['title'], entry['url']))
		return result

	@staticmethod
	def split_list(lst, n):
		return [lst[i:i + n] for i in range(0, len(lst), n)]

	@staticmethod
	def sort(lst, reverse=False):
		return sorted(lst, reverse=reverse)

	@staticmethod
	def merge_list(old_list, new_list):
		updated_list = []
		if not isinstance(old_list, list) and not isinstance(new_list, list):
			return updated_list
		for old_item, new_item in zip_longest(old_list, new_list, fillvalue=None):
			if old_item != new_item:
				if old_item and new_item and len(old_item) < len(new_item):
					old_item[:2] = new_item[:2]
					old_item.extend(new_item[2:])
				elif old_item and new_item:
					old_item[:2] = new_item[:2]
					updated_list.append(old_item)
				#elif old_item and not new_item:
				elif not old_item and new_item:
					updated_list.append(new_item)
		if not updated_list:
			print('Warning: do not merge two lists with different structures.')
		return updated_list

class Query:
	def __init__(self, CASE=False):
		self.case = CASE

	@staticmethod
	def calculate_match_score(title, query):
		score = 0
		score += sum(1 for word in query if word in title)
		return score

	def search(self, data, query):
		query = query.lower()
		query = set(query.split())
		result = []
		for title, url in data:
			score = self.calculate_match_score(title if self.case else title.lower(), query)
			if score > 0:
				result.append((title, url, score))
		result.sort(key=lambda x: x[2], reverse=True)
		if not result:
			print('No matching playlist found.')
			OSManager.exit(404)
		return [(title, url) for title, url, _ in result]

class FileHandler:
	def __init__(self):
		self.filename = 'playlists.json'
		self.encoding = 'utf-8'

	def dump(self, video_list):
		with open(self.filename, 'w', encoding=self.encoding) as f:
			json.dump(video_list, f, indent=4)

	def load(self):
		with open(self.filename, 'r', encoding=self.encoding) as f:
			return json.load(f)

	def clear_cache(self):
		OSManager.delete_file(self.filename)

class HistoryHandler:
	def __init__(self):
		self.filename = 'history.json'
		self.encoding = 'utf-8'

	def is_history(self):
		return OSManager.exists(self.filename)

	def load(self):
		with open(self.filename, 'r', encoding=self.encoding) as f:
			return json.load(f)

	def update(self, curr='', playlist='', videos=''):
		is_history = self.is_history()
		if is_history:
			content = self.load()
		content = {
			'current': content['current'] if is_history and not curr else curr,
			'playlist': content['playlist'] if is_history and not playlist else playlist,
			'videos': content['videos'] if is_history and not videos else videos
		}

		with open(self.filename, 'w', encoding=self.encoding) as f:
			json.dump(content, f, indent=4)

	def search(self, curr_url, history):
		history = history['videos']
		for index in range(len(history)):
			if history[index][1] == curr_url:
				return index
		return -1

	def delete_history(self):
		OSManager.delete_file(self.filename)

class YT_DLP_Options:
	def __init__(self, quiet=True, no_warnings=True):
		self.ydl_opts = {
			'extract_flat': True,
			'force_generic_extractor': False,
			'quiet': quiet,
			'no_warnings': no_warnings
		}

class YT_DLP:
	def __init__(self, channel_url, ydl_options: YT_DLP_Options):
		self.channel_url = channel_url

		if self.channel_url:
			if not (bool((parsed_url := urlparse(self.channel_url)).scheme) and bool(parsed_url.netloc)):
				if self.channel_url[:2] == 'UC':
					self.channel_url = urljoin('https://www.youtube.com/channel/', self.channel_url)
				else:
					self.channel_url = urljoin('https://www.youtube.com/', self.channel_url)
			self.channel_url = urljoin(self.channel_url if self.channel_url.endswith('/') else self.channel_url + '/', 'playlists')
		self.ydl_options = ydl_options

	def get_playlist(self):
		try:
			if not self.channel_url:
				raise MissingChannelUrl('No channel url specified.')

			with yt_dlp.YoutubeDL(self.ydl_options.ydl_opts) as ydl:
				result = ydl.extract_info(self.channel_url, download=False)
			return result
		except yt_dlp.utils.DownloadError:
			OSManager.exit(404)

	def get_video(self, url):
		try:
			with yt_dlp.YoutubeDL(self.ydl_options.ydl_opts) as ydl:
				result = ydl.extract_info(url, download=False)
			return result
		except yt_dlp.utils.DownloadError:
			OSManager.exit(404)

	def get_stream(self, url):
		formats = self.get_video(url)
		return (formats['requested_formats'][0]['url'], formats['requested_formats'][1]['url'])

	@staticmethod
	def download(url, cats='all', extra_args=[], args=None):
		if args is None:
			args = [
				'--no-warnings',
				'--progress',
				'--sponsorblock-remove', cats,
				url
				]

		if extra_args:
			if isinstance(extra_args, str):
				args.append(extra_args)
			else:
				args += extra_args

		command = ['yt-dlp'] + args
		subprocess.run(command)

class Player:
	def __init__(self, url, args=None):
		if args is None:
			self.args = [
				'--input-conf=custom.conf'
				]
		else:
			self.args = args
		self.command = ['mpv'] + self.args + [url]
		
		self.android_command = [
			'am start',
			'-a', 'android.intent.action.VIEW',
			'-t', 'video/any',
			'-p', 'is.xyz.mpv',
			'-d', url,
		]

	def run_mpv(self): # optional: use sponsorblock for mpv to automatically skip op/en
		subprocess.run(self.command)

	def run_mpv_android(self): # require https://github.com/mpv-android/mpv-android/pull/58
		subprocess.run(self.android_command)

	def start(self):
		if OSManager.android_check():
			self.run_mpv_android()
		else:
			self.run_mpv()

class Display_Options:
	def __init__(self, items_per_list=12):
		self.items_per_list = items_per_list

class Display:
	def __init__(self, opts: Display_Options):
		self.opts = opts
		self.user_input = ''

	@staticmethod
	def search():
		return str(input('Search: '))

	@staticmethod
	def clscr():
		if sys.platform == "win32":
			os.system("cls")
		else:
			os.system("clear")

	def choose_menu(self, data):
		splited_data = DataProcessing.split_list(data, self.opts.items_per_list)
		len_data = len(splited_data)
		len_last_item = len(splited_data[len_data - 1])
		total_items = (self.opts.items_per_list * (len_data - 1)) + len_last_item

		index_item = 0
		show_link = False
		while True:
			self.clscr()

			if index_item >= len_data:
				index_item = 0

			if index_item == -1:
				index_item = len_data-1

			if len_data > 1:
				print('(N) Next page\n(P) Previous page\n(U) Show link\n(P:integer) Jump to the specified page.\n(Q) Quit\n')

			len_data_items = len(splited_data[index_item])
			print(f'Page: {index_item+1}/{len_data} ({len_data_items + index_item*self.opts.items_per_list}/{total_items})\n')

			for index in range(len_data_items):
				print(f'({index_item*self.opts.items_per_list + index + 1}){'*' if len(splited_data[index_item][index]) >= 3 and splited_data[index_item][index][2].lower() == 'viewed' else ''} {splited_data[index_item][index][0]}' + (f'\n\t{splited_data[index_item][index][1]}' if show_link else '') )

			self.user_input = input('\nSelect: ')

			if len(self.user_input) >= 3 and self.user_input[:2].lower() == 'p:' and (x := self.user_input[2:]).isdigit():
				index_item = int(x) - 1
			elif self.user_input.upper() == 'N':
				index_item += 1
			elif self.user_input.upper() == 'P':
				index_item -= 1
			elif self.user_input.upper() == 'U':
				show_link = not show_link
			elif self.user_input.upper() == 'Q':
				OSManager.exit()
			else:
				try:
					ans = data[int(self.user_input) - 1]
					return ans[0], ans[1]
				except ValueError:
					input('ValueError: only N, P, U, Q and non-negative integers are accepted.\n')
					pass
				except IndexError:
					input('IndexError: The requested item is not listed.\n')
					pass

###

class Main:
	def __init__(self, channel_url, opts='auto'):
		self.ydl_options = YT_DLP_Options()
		self.dlp = YT_DLP(channel_url, self.ydl_options)
		self.file_handler = FileHandler()
		self.history_handler = HistoryHandler()
		self.dp = DataProcessing
		self.query = Query()
		self.display_opts = Display(Display_Options())
		self.url = ''
		self.opts = opts.lower()

	def update(self):
		print('Getting playlist...')
		try:
			playlist = self.dlp.get_playlist()
			print('Saving...')
			playlist = self.dp.omit(playlist)
			self.file_handler.dump(playlist)
			print('Done!')
		except MissingChannelUrl:
			print(f'Playlist info or channel not found.\nTo get playlist info: {os.path.basename(__file__)} -c/--channel CHANNEL')
			OSManager.exit(404)

		if not self.history_handler.is_history():
			return

		print('Update history playlist...')
		history = self.history_handler.load()
		new_playlist = self.dlp.get_video(list(history['playlist'].values())[0])
		print('Saving...')
		new_playlist = self.dp.omit(new_playlist)
		new_playlist = self.dp.sort(new_playlist)
		new_playlist = self.dp.merge_list(history['videos'], new_playlist)
		self.history_handler.update(history['current'], history['playlist'], new_playlist)
		print('Done!')
		return

	def clear_cache(self):
		self.file_handler.clear_cache()

	def delete_history(self):
		self.history_handler.delete_history()

	def load_playlist(self):
		try:
			playlist = self.file_handler.load()
		except FileNotFoundError:
			self.update()
			playlist = self.file_handler.load()
		return playlist

	def start_player(self):
		player = Player(self.url)

		if self.opts == 'auto':
			player.start()
		elif self.opts == 'android':
			player.run_mpv_android()
		else:
			player.run_mpv()

	def loop(self):
		history = HistoryHandler().load()
		videos = history['videos']
		title, self.url = self.display_opts.choose_menu(videos)
		self.start_player()
		index = self.history_handler.search(self.url, history)
		videos[index] += ('viewed',)
		self.history_handler.update({title:self.url}, None, videos)
		self.loop()

	def menu(self, video):
		playlist_title, url = self.display_opts.choose_menu(video)
		video = self.dlp.get_video(url)
		video = self.dp.omit(video)
		videos = self.dp.sort(video)
		title, self.url = self.display_opts.choose_menu(videos)
		self.history_handler.update({title:self.url}, {playlist_title: url}, videos)
		self.start_player()
		history = HistoryHandler().load()
		videos = history['videos']
		index = self.history_handler.search(self.url, history)
		videos[index] += ('viewed',)
		self.history_handler.update({title:self.url}, None, videos)
		self.loop()

	def list(self):
		playlist = self.load_playlist()
		self.menu(playlist)

	def resume(self):
		history = HistoryHandler().load()
		history = history['current']
		self.url = list(history.values())[0]
		self.start_player()
		self.loop()

	def search(self, inp):
		playlist = self.load_playlist()
		playlist = self.query.search(playlist, inp)
		self.menu(playlist)

class ArgsHandler:
	def __init__(self):
		self.parser = argparse.ArgumentParser(description='Note: Arguments, if provided, will be processed sequentially in the order they are listed below.')
		self.parser.add_argument('-c', '--channel', type=str, help='Create or Update Playlist Data from Link, Channel ID, or Channel Handle.')
		self.parser.add_argument('--mpv-player', type=str, choices=['auto', 'android'], default='auto', help='MPV player mode.')
		self.parser.add_argument('--clear-cache', action='store_const', const='clear_cache', help='Clear cache.')
		self.parser.add_argument('--delete-history', action='store_const', const='delete_history', help='Delete history.')
		self.parser.add_argument('-l', '--list', action='store_const', const='list', help='Browse all cached playlists.')
		self.parser.add_argument('-v', '--viewed-mode', action='store_const', const='viewed-mode', help='Browse all videos in cached playlist. Cached playlists will be cleared after playlist selection.')
		self.parser.add_argument('-r', '--resume', action='store_const', const='resume', help='View last viewed video.')
		self.parser.add_argument('-s', '--search', type=str, help='Search for a playlist.')

		self.args = self.parser.parse_args()

		self.main = Main(self.args.channel, self.args.mpv_player)
		if self.args.channel:
			self.main.update()

		self.actions = {
			'clear_cache': self.main.clear_cache,
			'delete_history': self.main.delete_history,
			'list': self.main.list,
			'viewed-mode': self.main.loop,
			'resume': self.main.resume
		}

	def run_main(self, action):
		try:
			return self.actions.get(action)()
		except TypeError as e:
			print(e)
			OSManager.exit(404)

	def listener(self):
		action_lst = [getattr(self.args, item, None) for item in list(self.actions.keys())]

		for action in action_lst:
			if action:
				self.run_main(action)

		if action := self.args.search:
			self.main.search(action)

def main():
	ArgsHandler().listener()

if __name__ == '__main__':
	main()