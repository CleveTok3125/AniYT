from urllib.parse import urljoin, urlparse
import json
import subprocess
import os
import sys
import argparse

import yt_dlp
from rapidfuzz import process

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
	def sort(lst, key=lambda x: x[0], reverse=False):
		return sorted(lst, key=key, reverse=reverse)

	@staticmethod
	def merge_list(old_list, new_list, truncate=True):
		mapping = {v: k for k, v in new_list}

		if truncate:
			old_list = [sublist for sublist in old_list if sublist[1] in set(mapping.keys())]

		for old_list_item in old_list:
			if old_list_item[1] in mapping:
				old_list_item[0] = mapping[old_list_item[1]]

		existing_values = {sublist[1] for sublist in old_list}

		for k, v in new_list:
			if v not in existing_values:
				old_list.append([k, v])

		return DataProcessing.sort(old_list)

class Query:
	def __init__(self, CASE=False):
		self.case = CASE

	@staticmethod
	def calculate_match_score(title, query):
		score = 0
		score += sum(1 for word in query if word in title)
		return score

	def search(self, data, query):
		if not self.case:
			query = query.lower()
		query = set(query.split())
		result = []
		for title, url in data:
			score = self.calculate_match_score(title if self.case else title.lower(), query)
			if score > 0:
				result.append((title, url, score))
		result = DataProcessing.sort(result, key=lambda x: x[2], reverse=True)
		return [(title, url) for title, url, _ in result]

	def fuzzysearch(self, data, query, score=50):
		if not self.case:
			query = query.lower()
		result = process.extract(query, [item[0] if self.case else item[0].lower() for item in data], limit=None)

		results_with_data = []
		for match in result:
			matched_name = match[0]
			matched_score = match[1]

			matched_item = next(
				(item for item in data if
					(item[0] if self.case else item[0].lower()) == matched_name and matched_score > score),
				None
			)

			if matched_item:
				results_with_data.append((matched_item[0], matched_item[1], matched_score))
		results_with_data = DataProcessing.sort(results_with_data, key=lambda x: x[2], reverse=True)
		return [(title, url) for title, url, _ in results_with_data]

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

class BookmarkingHandler:
	def __init__(self):
		self.filename = 'bookmark.json'
		self.encoding = 'utf-8'

	def is_bookmarking(self):
		return OSManager.exists(self.filename)

	def load(self):
		with open(self.filename, 'r', encoding=self.encoding) as f:
			return json.load(f)

	def update(self, data):
		if self.is_bookmarking():
			content = self.load()
		else:
			content = {}

		content[data[0]] = data[1]

		with open(self.filename, 'w', encoding=self.encoding) as f:
			json.dump(content, f, indent=4)

	def is_bookmarked(self, url):
		if not self.is_bookmarking():
			return False
		content = self.load()
		return url in content.values()

	def remove_bookmark(self, url):
		if not self.is_bookmarking():
			return
		content = self.load()
		for key, value in list(content.items()):
			if value == url:
				del content[key]
				break
		with open(self.filename, 'w', encoding=self.encoding) as f:
			json.dump(content, f, indent=4)

	def delete_bookmark(self):
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
			'am', 'start',
			'-a', 'android.intent.action.VIEW',
			'-t', 'video/any',
			'-p', 'is.xyz.mpv.ytdl',
			'-d', url,
		]

	def run_mpv(self): # optional: use sponsorblock for mpv to automatically skip op/en
		try:
			result = subprocess.run(self.command)
		except FileNotFoundError:
			print('Error running command: MPV is not installed.')
			OSManager.exit(127)

	def run_mpv_android(self): # require https://github.com/mpv-android/mpv-android/pull/58
		try:
			subprocess.run(self.android_command)
		except FileNotFoundError:
			print('Error running command: Current OS may not be Android.')
			OSManager.exit(127)

	def start(self):
		if OSManager.android_check():
			self.run_mpv_android()
		else:
			self.run_mpv()

class Display_Options:
	def __init__(self, items_per_list=12):
		self.items_per_list = items_per_list
		self.show_opts = False
		self.show_link = False
		self.bookmark = True

class Display:
	@staticmethod
	def search():
		return str(input('Search: '))

	@staticmethod
	def clscr():
		if sys.platform == "win32":
			os.system("cls")
		else:
			os.system("clear")

class DisplayMenu(Display):
	def __init__(self, opts: Display_Options):
		self.bookmarking_handler = BookmarkingHandler()

		# Variable
		# These values are always created new each time the class is called or are always overwritten.
		self.opts = opts
		self.user_input = ''
		self.data = []
		self.splited_data = []
		self.len_data = 0
		self.len_last_item = 0
		self.total_items = 0
		self.len_data_items = 0

		# Constant
		self.no_opts = ['(O) Hide all options', '(O) Show all options']
		self.pages_opts = ['(N) Next page', '(P) Previous page', '(P:<integer>) Jump to page']
		self.page_opts = [self.no_opts[0], '(U) Toggle link', '(B) Toggle bookmark', '(B:<integer>) Add/remove bookmark', '(I:<integer>) number of items per page', '(Q) Quit']
		self.pages_opts = '\n'.join(self.pages_opts)
		self.page_opts = '\n'.join(self.page_opts)

		# Constant
		self.RESET = '\033[0m'
		self.YELLOW = '\033[33m'
		self.LIGHT_GRAY = '\033[38;5;247m'

		# Variable
		self._init_loop_values_()

	def _init_loop_values_(self):
		'''
		These values are used to process in the while loop.
		Whenever the while loop exits, these values need to be reset if the associated function is to be reused.
		
		def example(lst):
			index_item = 0
			show_link = False
			bookmark = True
			while index_item < 10:
				print(lst[index_item] + 'link' if show_link else lst[index_item] + 'bookmark' if bookmark else lst[index_item])

		The values of index_item, show_link and bookmark will always be reset each time the function is called.
		Calling the class every time will not have the problem of instance attributes but will have performance problems.
		'''
		self.index_item = 0
		self.show_link = self.opts.show_link
		self.bookmark = self.opts.bookmark

	def valid_index_item(self):
		if self.index_item >= self.len_data:
			self.index_item = 0
		elif self.index_item <= -1:
			self.index_item = self.len_data-1

	def pagination(self):
		self.valid_index_item()

		self.splited_data = DataProcessing.split_list(self.data, self.opts.items_per_list)
		self.len_data = len(self.splited_data)
		self.len_last_item = len(self.splited_data[self.len_data - 1])
		self.total_items = (self.opts.items_per_list * (self.len_data - 1)) + self.len_last_item
		self.splited_data_items = self.splited_data[self.index_item]

	def print_option(self):
		if self.opts.show_opts:
			if self.len_data > 1:
				output = f'{self.pages_opts}\n{self.page_opts}'
			else:
				output = self.page_opts
		else:
			output = self.no_opts[1]
		print(f'{output}\n')

	def print_page_indicator(self):
		showed_item = self.len_data_items + self.index_item*self.opts.items_per_list
		print(f'Page: {self.index_item+1}/{self.len_data} ({showed_item}/{self.total_items})\n')

	def print_menu(self):
		for index in range(self.len_data_items):
			item = self.splited_data_items[index]
			item_title = item[0]
			item_url = item[1]

			color_viewed = self.LIGHT_GRAY if len(item) >= 3 and item[2].lower() == 'viewed' else ''
			color_bookmarked = self.YELLOW if self.bookmark and self.bookmarking_handler.is_bookmarked(item_url) else ''

			item_number = self.index_item*self.opts.items_per_list + index + 1
			link = f'\n\t{item_url}' if self.show_link else ''

			print(f'{self.RESET}{color_viewed}{color_bookmarked}({item_number}) {item_title}{link}{self.RESET}')
		print()

	def print_user_input(self):
		try:
			self.user_input = input('Select: ')
		except KeyboardInterrupt:
			OSManager.exit(0)

	def bookmark_processing(self, user_int):
		try:
			if self.bookmarking_handler.is_bookmarked((item := self.data[user_int - 1])[1]):
				self.bookmarking_handler.remove_bookmark(item[1])
			else:
				self.bookmarking_handler.update(item)
		except ValueError:
			input('ValueError: only non-negative integers are accepted.\n')
		except IndexError:
			input('IndexError: The requested item is not listed.\n')

	def advanced_options(self):
		if len(self.user_input) >= 3 and (user_int := self.user_input[2:]).isdigit():
			user_int = int(user_int)
			user_input = self.user_input[:2].upper()
			if user_input == 'P:':
				self.index_item = user_int - 1
			elif user_input == 'B:':
				self.bookmark_processing(user_int)
			elif user_input == 'I:':
				self.opts.items_per_list = user_int if user_int > 0 else self.total_items if user_int > self.total_items else 1
			else:
				return False
			return True
		return False

	def standard_options(self):
		user_input = self.user_input.upper()
		if user_input == 'O':
			self.opts.show_opts = not self.opts.show_opts
		elif user_input == 'N':
			self.index_item += 1
		elif user_input == 'P':
			self.index_item -= 1
		elif user_input == 'U':
			self.show_link = not self.show_link
		elif user_input == 'B':
			self.bookmark = not self.bookmark
		elif user_input == 'Q':
			OSManager.exit(0)
		else:
			try:
				ans = self.data[int(self.user_input) - 1]
				return ans[0], ans[1]
			except ValueError:
				input('ValueError: only options and non-negative integers are accepted.\n')
			except IndexError:
				input('IndexError: The requested item is not listed.\n')
		return

	def choose_menu(self, data):
		self.data = data
		self.pagination()

		try:
			while True:
				self.clscr()

				self.valid_index_item()

				self.splited_data_items = self.splited_data[self.index_item]
				self.len_data_items = len(self.splited_data_items)

				self.print_option()
				self.print_page_indicator()
				self.print_menu()
				self.print_user_input()

				if self.advanced_options():
					continue

				if ans := self.standard_options():
					return ans
				else:
					continue
		finally:
			self._init_loop_values_()

###

class Main:
	def __init__(self, channel_url, opts='auto'):
		self.ydl_options = YT_DLP_Options()
		self.dlp = YT_DLP(channel_url, self.ydl_options)
		self.file_handler = FileHandler()
		self.history_handler = HistoryHandler()
		self.bookmarking_handler = BookmarkingHandler()
		self.dp = DataProcessing
		self.display_opts = Display_Options()
		self.display_menu = DisplayMenu(self.display_opts)
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
		new_playlist = self.dp.merge_list(history['videos'], new_playlist)
		self.history_handler.update(history['current'], history['playlist'], new_playlist)
		print('Done!')
		return

	def clear_cache(self):
		self.file_handler.clear_cache()

	def delete_history(self):
		self.history_handler.delete_history()

	def delete_bookmark(self):
		self.bookmarking_handler.delete_bookmark()

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
		title, self.url = self.display_menu.choose_menu(videos)
		self.start_player()
		index = self.history_handler.search(self.url, history)
		videos[index] += ('viewed',)
		self.history_handler.update({title:self.url}, None, videos)
		self.loop()

	def menu(self, video):
		playlist_title, url = self.display_menu.choose_menu(video)
		video = self.dlp.get_video(url)
		video = self.dp.omit(video)
		videos = self.dp.sort(video)
		title, self.url = self.display_menu.choose_menu(videos)
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

	def search(self, inp, case_sensitive=False, fuzzy=False, score=50):
		query = Query(CASE=case_sensitive)
		playlist = self.load_playlist()
		
		if fuzzy:
			playlist = query.fuzzysearch(playlist, inp, score)
		else:
			playlist = query.search(playlist, inp)
		
		if not playlist:
			print('No matching playlist found.')
			return
		self.menu(playlist)

class ArgsHandler:
	def __init__(self):
		self.parser = argparse.ArgumentParser(description='Note: Options, if provided, will be processed sequentially in the order they are listed below.')

		self.parser.add_argument('-c', '--channel', type=str, help='Create or Update Playlist Data from Link, Channel ID, or Channel Handle.')
		self.parser.add_argument('--mpv-player', type=str, choices=['auto', 'android'], default='auto', help='MPV player mode.')
		self.parser.add_argument('--clear-cache', action='store_const', const='clear_cache', help='Clear cache.')
		self.parser.add_argument('--delete-history', action='store_const', const='delete_history', help='Delete history.')
		self.parser.add_argument('--delete-bookmark', action='store_const', const='delete_bookmark', help='Delete bookmark.')
		self.parser.add_argument('-l', '--list', action='store_const', const='list', help='Browse all cached playlists.')
		self.parser.add_argument('-v', '--viewed-mode', action='store_const', const='viewed_mode', help='Browse all videos in cached playlist. Cached playlists will be cleared after playlist selection.')
		self.parser.add_argument('-r', '--resume', action='store_const', const='resume', help='View last viewed video.')

		self.subparsers = self.parser.add_subparsers(dest='command', help='Note: To avoid incorrect handling, positional arguments should be placed after all options.')
		self.download_parsers = self.subparsers.add_parser('download', help='Download video and skip sponsors using SponsorBlock.')
		self.download_parsers.add_argument('url', type=str, help='Video url.')
		self.download_parsers.add_argument('-cat', '--category', type=str, default='all', help='See https://wiki.sponsor.ajay.app/w/Types#Category.')

		self.search_parsers = self.subparsers.add_parser('search', help='Search for a playlist.')
		self.search_parsers.add_argument('query', type=str, help='Search content.')
		self.search_parsers.add_argument('-C', '--case-sensitive', action='store_true', help='Case sensitive.')
		self.search_parsers.add_argument('-fs', '--fuzzysearch', action='store_true', help='Fuzzy search.')
		self.search_parsers.add_argument('-s', '--score', type=int, default=50, help='The accuracy of fuzzy search (0-100).')

		self.args = self.parser.parse_args()

		self.main = Main(self.args.channel, self.args.mpv_player)
		if self.args.channel:
			self.main.update()

		self.actions = {
			'clear_cache': self.main.clear_cache,
			'delete_history': self.main.delete_history,
			'delete_bookmark': self.main.delete_bookmark,
			'list': self.main.list,
			'viewed_mode': self.main.loop,
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

		if self.args.command == 'search':
			self.main.search(self.args.query, self.args.case_sensitive, fuzzy=self.args.fuzzysearch, score=self.args.score)

		if self.args.command == 'download':
			YT_DLP.download(self.args.url, self.args.category)

def main():
	ArgsHandler().listener()

if __name__ == '__main__':
	main()