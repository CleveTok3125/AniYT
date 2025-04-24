from urllib.parse import urljoin, urlparse
import json
import subprocess
import os
import sys
import argparse
from tempfile import mkdtemp
from time import sleep

import yt_dlp
from rapidfuzz import process

# Extension
import requests

class Extension:
	class CheckModuleUpdate:
		@staticmethod
		def check_yt_dlp(name='yt-dlp'):
			old_ver = subprocess.check_output(['yt-dlp', '--version']).decode('utf-8').strip()
			old_ver = '.'.join(str(int(part)) for part in old_ver.split('.'))
			new_ver = requests.get('https://pypi.org/pypi/yt-dlp/json').json()['info']['version']
			return (old_ver == new_ver, name, old_ver, new_ver)

		@staticmethod
		def print_notice(update_info):
			if not update_info[0]:
				print(f'\n\033[34m[notice]\033[0m A new release of {update_info[1]} is available: \033[31m{update_info[2]}\033[0m -> \033[32m{update_info[3]}\033[0m')
				print(f'\033[34m[notice]\033[0m To update, run: \033[32mpython -m pip install --upgrade {update_info[1]}\033[0m')

	@staticmethod
	def check_module_update(func):
		def wrapper(*args, **kwargs):
			yt_dlp_update_info = Extension.CheckModuleUpdate.check_yt_dlp()
			Extension.CheckModuleUpdate.print_notice(yt_dlp_update_info)

			return func(*args, **kwargs)
		return wrapper

class MissingChannelUrl(Exception):
	pass

class OSManager:
	@Extension.check_module_update
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

	@staticmethod
	def temporary_session():
		temp_path = mkdtemp(prefix='AniYT_')
		os.chdir(temp_path)
		return temp_path

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
		return info['thumbnails'][-1]['url']

	def get_stream(self, url):
		formats = self.get_video(url)
		return (formats['requested_formats'][0]['url'], formats['requested_formats'][1]['url'])

	@staticmethod
	def download(url, cats='all', extra_args=[], args=None, capture_output=False):
		if args is None:
			args = [
				'--no-warnings',
				'--progress',
				'--sponsorblock-remove', cats,
				url,
				'--output', os.path.join(os.getcwd(), '%(title)s [%(id)s].%(ext)s'),
				'--print', 'after_move:filepath'
				]

		if extra_args:
			if isinstance(extra_args, str):
				args.append(extra_args)
			else:
				args += extra_args

		command = ['yt-dlp'] + args
		result = subprocess.run(command, capture_output=capture_output)
		return result.stdout

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
			'-d', url
		]

	def run_mpv(self): # optional: use sponsorblock for mpv to automatically skip op/en
		try:
			subprocess.run(self.command)
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

	@staticmethod
	def start_with_mode(url, opts='auto'):
		print('Playing...')

		player = Player(url)

		if opts == 'auto':
			player.start()
		elif opts == 'android':
			player.run_mpv_android()
		elif opts == 'ssh':
			print('Copy one of the commands below:')
			print(f'MPV: \n\n\t{' '.join(player.command)}\n\nMPV Android: \n\n\t{' '.join(player.android_command)}\n\n')
			try:
				input('Press Enter to continue...\t')
			except KeyboardInterrupt:
				pass
		else:
			player.run_mpv()

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

class DisplayExtensionFallback:
	# Ensures the program still works even if the extension cannot be loaded

    @staticmethod
    def fallback_bookmark_handler():
        # Mock BookmarkingHandler for fallback purposes
        class MockBookmarkingHandler(BookmarkingHandler):
            def __init__(self):
                pass  # No need to reinitialize attributes, just override methods as needed

            def is_bookmarked(self, url):
                # Override the method to always return False (or any desired value for mock)
                return False

            def remove_bookmark(self, url):
                # Mock the behavior of removing a bookmark
                print(f"[Mock] Removed bookmark for: {url}")

            def update(self, data):
                # Mock the behavior of updating a bookmark
                print(f"[Mock] Updated bookmark: {data}")

        return MockBookmarkingHandler()

    @staticmethod
    def fallback_yt_dlp_opts():
        return YT_DLP_Options(quiet=True, no_warnings=True)

class DisplayExtension:
	def _inject_dependencies(self): # Only used when you want to declare an instance, other values ​​like str, int, list, etc can be taken directly from extra_opts
		self.bookmarking_handler = self._get_dependencies(
			'bookmark1', BookmarkingHandler,
			fallback_factory=DisplayExtensionFallback.fallback_bookmark_handler)

		self.yt_dlp_opts = self._get_dependencies(
			'yt-dlp1', YT_DLP_Options,
			fallback_factory=DisplayExtensionFallback.fallback_yt_dlp_opts)

	def _init_extra_opts(self, extra_opts):
		self.extra_opts = extra_opts

		if not isinstance(extra_opts, dict):
			raise TypeError(f"The parameter passed should be a dictionary, but got {type(extra_opts)}")

	def _get_dependencies_errors(self, requirement, requirement_suggestion, dependency):
		if not dependency:
			raise ValueError(f"Missing required dependency: '{requirement}' is not provided. Need instance of class {requirement_suggestion}")
		elif not isinstance(dependency, requirement_suggestion):
			raise TypeError(f"Instance {dependency} is not an instance of class {requirement_suggestion}")
		elif isinstance(dependency, type):
			raise TypeError(f"The dependency '{requirement}' should be an instance, but got a class: {dependency}")
		elif dependency.__class__.__module__ == "builtins":
			raise TypeError(f"The dependency '{requirement}' should be an instance of a user-defined class, but got built-in type: {type(dependency)}")

	def _get_dependencies(self, requirement: object, requirement_suggestion: type, fallback_factory=None):
		dependency = self.extra_opts.get(requirement)
		strict_mode = self.extra_opts.get('strict_mode', False)
		default_warning_time = 1
		warning_time = self.extra_opts.get('warning_time', default_warning_time)

		if not isinstance(strict_mode, bool):
			strict_mode = False

		if isinstance(warning_time, str):
			warning_time = int(warning_time) if warning_time.isdigit() else default_warning_time
		elif not isinstance(warning_time, int):
			warning_time = default_warning_time

		if strict_mode:
			print(f"[StrictMode] Checking '{requirement}' strictly.")
			self._get_dependencies_errors(requirement, requirement_suggestion, dependency)
		else:
			try:
				self._get_dependencies_errors(requirement, requirement_suggestion, dependency)
			except (ValueError, TypeError) as e:
				if fallback_factory:
					print(f"{type(e).__name__}: {e}")
					fallback = fallback_factory()

					if not isinstance(fallback, requirement_suggestion):
						raise TypeError(f"Fallback for '{requirement}' is not valid instance of {requirement_suggestion}")

					print(f"[WARN] Using fallback for '{requirement}': {fallback.__class__.__name__}")
					self.extra_opts[requirement] = fallback
					dependency = fallback

					if warning_time == -1:
						input()
					else:
						sleep(warning_time)

		return dependency

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

	def open_image_with_mpv(self, url):
		Player.start_with_mode(url=url, opts=self.extra_opts.get('mode', 'auto'))

	def show_thumbnail(self, user_int):
		url = self.data[user_int - 1][1]

		thumbnail_url = YT_DLP.standalone_get_thumbnail(url, self.yt_dlp_opts.ydl_opts)
		self.open_image_with_mpv(thumbnail_url)

class DisplayMenu(Display, DisplayExtension):
	def __init__(self, opts: Display_Options, extra_opts = {}):
		# Dependencies
		self._init_extra_opts(extra_opts) # Some features require additional settings, use it to pass in user settings. Related features should be implemented in DisplayExtension.
		self._inject_dependencies()

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
		self.clear_choosed_item = False

		# Variable
		# These are variables that are manually cleared for caching purposes. Remember to clear these variables when running functions in the class multiple times.
		self.choosed_item = False

		# Constant
		self.no_opts = ['(O) Hide all options', '(O) Show all options']
		self.pages_opts = ['(N) Next page', '(P) Previous page', '(P:<integer>) Jump to page']
		self.page_opts = [self.no_opts[0], '(U) Toggle link', '(B) Toggle bookmark', '(B:<integer>) Add/remove bookmark', '(T:<integer>) View thumbnail', '(I:<integer>) number of items per page', '(Q) Quit']
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
		if self.choosed_item >= self.len_data:
			self.choosed_item = False

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
		skip_choose_item = False

		for index in range(self.len_data_items):
			item = self.splited_data_items[index]
			item_title = item[0]
			item_url = item[1]

			item_number = self.index_item*self.opts.items_per_list + index + 1 

			color_viewed = ''
			if len(item) >= 3 and item[2].lower() == 'viewed': 
				color_viewed = self.LIGHT_GRAY
			elif not skip_choose_item:
				skip_choose_item = True
				self.choosed_item = item_number - 1

			color_bookmarked = self.YELLOW if self.bookmark and self.bookmarking_handler.is_bookmarked(item_url) else ''

			link = f'\n\t{item_url}' if self.show_link else ''

			print(f'{self.RESET}{color_viewed}{color_bookmarked}({item_number}) {item_title}{link}{self.RESET}')
		print()

	def print_user_input(self):
		try:
			self.user_input = input('Select: ').strip()
		except KeyboardInterrupt:
			OSManager.exit(0)

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
				self.pagination()
			elif user_input == 'T:':
				self.show_thumbnail(user_int)
			else:
				return False
			return True
		return False

	def choose_item_option(self):
		try:
			if self.clear_choosed_item:
				self.choosed_item = False

			if self.user_input == '':
				self.choosed_item += 1
				self.user_input = str(self.choosed_item)
				return self.choose_item_option()

			if not self.user_input.isdigit():
				raise ValueError()

			self.choosed_item = int(self.user_input)
			ans = self.data[self.choosed_item - 1]
			return ans[0], ans[1]

		except ValueError:
			input('ValueError: only options and non-negative integers are accepted.\n')
		except IndexError:
			input('IndexError: The requested item is not listed.\n')
		return

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
			return self.choose_item_option()
		return

	def choose_menu(self, data, clear_choosed_item=False):
		'''
		How auto-select (guessing user choices) feature works
		1. __init__()
		Initialize self.choosed_item
		2. print_menu()
		Assign a default value to self.choosed_item
		This value is the index of the latest episode the user has watched
		If not, self.choosed_item retains its initial value
		3. choose_item_option()
		If the user specifies a specific number (for self.user_input), it overwrites the default value of self.choosed_item
		If not, self.choosed_item is incremented by 1 (the index of the next episode) and overwrites self.user_input
		When the value of self.choosed_item is the initial value, it is automatically processed as index 0 and returns a value of 1 (the first episode in the list)
		4. valid_index_item()
		In case self.choosed_item exceeds the valid limit, it will be set to its initial value.
		'''

		self.data = data
		self.clear_choosed_item = clear_choosed_item
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
		self.opts = opts.lower()
		self.ydl_options = YT_DLP_Options()
		self.dlp = YT_DLP(channel_url, self.ydl_options)
		self.file_handler = FileHandler()
		self.history_handler = HistoryHandler()
		self.bookmarking_handler = BookmarkingHandler()
		self.dp = DataProcessing
		self.display_opts = Display_Options()
		self.display_menu = DisplayMenu(self.display_opts, extra_opts={
			'yt-dlp': self.ydl_options,
			'mode': self.opts,
			'bookmark': self.bookmarking_handler})
		self.url = ''

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

	def start_player(self, url=None):
		if url:
			self.url = url
		Player.start_with_mode(url=self.url, opts=self.opts)

	def loop(self):
		while True:
			history = HistoryHandler().load()
			videos = history['videos']
			title, self.url = self.display_menu.choose_menu(videos)
			self.start_player()
			index = self.history_handler.search(self.url, history)
			if len(videos[index]) == 2:
				videos[index] += ('viewed',)
			self.history_handler.update({title:self.url}, None, videos)

	def menu(self, video):
		playlist_title, url = self.display_menu.choose_menu(video)
		video = self.dlp.get_video(url)
		video = self.dp.omit(video)
		videos = self.dp.sort(video)
		title, self.url = self.display_menu.choose_menu(videos, clear_choosed_item=True)
		self.history_handler.update({title:self.url}, {playlist_title: url}, videos)
		self.start_player()
		history = HistoryHandler().load()
		videos = history['videos']
		index = self.history_handler.search(self.url, history)
		videos[index] += ('viewed',)
		self.history_handler.update({title:self.url}, None, videos)
		self.loop()

	def show_bookmark(self):
		bms = self.bookmarking_handler.load()
		for key, value in bms.items():
			print(f'{self.display_menu.YELLOW}{key}{self.display_menu.RESET}\n\t{value}')

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

	def playlist_from_url(self, url):
		video = self.dlp.get_video(url)
		video = self.dp.omit(video)
		videos = self.dp.sort(video)
		_, self.url = self.display_menu.choose_menu(videos)
		self.start_player()

	def download(self, url, category, mpv):
		capture_output = (mpv == 'mpv')
		result = YT_DLP.download(url, category, capture_output=capture_output)
		
		if OSManager.android_check():
			return

		if result and capture_output:
			result = result.decode().split('\r')[-1].strip()
			self.start_player(result)
		elif not result and not capture_output:
			pass
		else:
			print('No data returned. There was an error downloading the video or it was already downloaded.')

	def open_with_mpv(self, inp):
		self.start_player(inp)

class ArgsHandler:
	def __init__(self):
		self.parser = argparse.ArgumentParser(description='Note: Options, if provided, will be processed sequentially in the order they are listed below.')

		self.parser.add_argument('-t', '--temp', action='store_const', const='store_true', help='Use temporary folder.')
		self.parser.add_argument('-c', '--channel', type=str, help='Create or Update Playlist Data from Link, Channel ID, or Channel Handle.')
		self.parser.add_argument('--mpv-player', type=str, choices=['auto', 'default', 'android', 'ssh'], default='auto', help='MPV player mode.')
		self.parser.add_argument('--clear-cache', action='store_const', const='clear_cache', help='Clear cache.')
		self.parser.add_argument('--delete-history', action='store_const', const='delete_history', help='Delete history.')
		self.parser.add_argument('--delete-bookmark', action='store_const', const='delete_bookmark', help='Delete bookmark.')
		self.parser.add_argument('-b', '--bookmark', action='store_const', const='bookmark', help='Show bookmark.')
		self.parser.add_argument('-l', '--list', action='store_const', const='list', help='Browse all cached playlists.')
		self.parser.add_argument('-v', '--viewed-mode', action='store_const', const='viewed_mode', help='Browse all videos in cached playlist. Cached playlists will be cleared after playlist selection.')
		self.parser.add_argument('-r', '--resume', action='store_const', const='resume', help='View last viewed video.')

		self.subparsers = self.parser.add_subparsers(dest='command', help='Note: To avoid incorrect handling, positional arguments should be placed after all options.')
		self.download_parsers = self.subparsers.add_parser('download', help='Download video and skip sponsors using SponsorBlock.')
		self.download_parsers.add_argument('url', type=str, help='Video url.')
		self.download_parsers.add_argument('-cat', '--category', type=str, default='all', help='See https://wiki.sponsor.ajay.app/w/Types#Category.')
		self.download_parsers.add_argument('-m', '--mpv', action='store_const', const='mpv', help='Open downloaded video with MPV. Download progress will not be displayed.')

		self.mpv_parsers = self.subparsers.add_parser('mpv', help='Open with MPV.')
		self.mpv_parsers.add_argument('input', type=str, help='Video url or file path. File path are currently not supported on Android.')

		self.search_parsers = self.subparsers.add_parser('search', help='Search for a playlist.')
		self.search_parsers.add_argument('query', type=str, help='Search content.')
		self.search_parsers.add_argument('-C', '--case-sensitive', action='store_true', help='Case sensitive.')
		self.search_parsers.add_argument('-fs', '--fuzzysearch', action='store_true', help='Fuzzy search.')
		self.search_parsers.add_argument('-s', '--score', type=int, default=50, help='The accuracy of fuzzy search (0-100).')

		self.playlist_parsers = self.subparsers.add_parser('playlist', help='Open playlist from URL')
		self.playlist_parsers.add_argument('url', type=str)

		self.args = self.parser.parse_args()

		if self.args.temp:
			temp_path = OSManager.temporary_session()
			print(temp_path)

		self.main = Main(self.args.channel, self.args.mpv_player)
		if self.args.channel:
			self.main.update()

		self.actions = {
			'clear_cache': self.main.clear_cache,
			'delete_history': self.main.delete_history,
			'delete_bookmark': self.main.delete_bookmark,
			'bookmark': self.main.show_bookmark,
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

		if not any(action_lst) and not self.args.command:
			self.parser.print_help()
			OSManager.exit(0)

		for action in action_lst:
			if action:
				self.run_main(action)

		if self.args.command == 'download':
			self.main.download(self.args.url, self.args.category, self.args.mpv)

		if self.args.command == 'mpv':
			self.main.open_with_mpv(self.args.input)

		if self.args.command == 'search':
			self.main.search(self.args.query, self.args.case_sensitive, fuzzy=self.args.fuzzysearch, score=self.args.score)

		if self.args.command == 'playlist':
			self.main.playlist_from_url(self.args.url)

		OSManager.exit(0)

def main():
	ArgsHandler().listener()

if __name__ == '__main__':
	main()
