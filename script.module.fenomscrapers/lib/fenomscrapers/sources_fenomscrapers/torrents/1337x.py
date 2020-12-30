# -*- coding: utf-8 -*-
# modified by Venom for Fenomscrapers (updated 12-23-2020)
'''
	Fenomscrapers Project
'''

import re
try: from urlparse import parse_qs, urljoin
except ImportError: from urllib.parse import parse_qs, urljoin
try: from urllib import urlencode, quote, unquote_plus
except ImportError: from urllib.parse import urlencode, quote, unquote_plus

from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils
from fenomscrapers.modules import workers


class source:
	def __init__(self):
		self.priority = 5
		self.language = ['en', 'de', 'fr', 'ko', 'pl', 'pt', 'ru']
		self.domains = ['1337x.to', '1337x.st', '1337x.ws', '1337x.eu', '1337x.se', '1337x.is'] # all are behind cloudflare except .to
		self.base_link = 'https://1337x.to/'
		self.tvsearch = 'https://1337x.to/sort-category-search/%s/TV/size/desc/1/'
		self.moviesearch = 'https://1337x.to/sort-category-search/%s/Movies/size/desc/1/'
		self.min_seeders = 1
		self.pack_capable = False


	def movie(self, imdb, title, aliases, year):
		try:
			url = {'imdb': imdb, 'title': title, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			return


	def tvshow(self, imdb, tvdb, tvshowtitle, aliases, year):
		try:
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			return


	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if not url: return
			url = parse_qs(url)
			url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
			url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
			url = urlencode(url)
			return url
		except:
			return


	def sources(self, url, hostDict):
		self._sources = []
		self.items = []
		if not url: return self._sources
		try:
			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			self.title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			self.title = self.title.replace('&', 'and').replace('Special Victims Unit', 'SVU')
			self.aliases = data['aliases']
			self.episode_title = data['title'] if 'tvshowtitle' in data else None
			self.hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']
			self.year = data['year']

			query = '%s %s' % (self.title, self.hdlr)
			query = re.sub('[^A-Za-z0-9\s\.-]+', '', query)
			urls = []
			if 'tvshowtitle' in data:
				urls.append(self.tvsearch % (quote(query)))
			else:
				urls.append(self.moviesearch % (quote(query)))
			url2 = ''.join(urls).replace('/1/', '/2/')
			urls.append(url2)
			# log_utils.log('urls = %s' % urls, log_utils.LOGDEBUG)

			threads = []
			for url in urls:
				threads.append(workers.Thread(self._get_items, url))
			[i.start() for i in threads]
			[i.join() for i in threads]

			threads2 = []
			for i in self.items:
				threads2.append(workers.Thread(self._get_sources, i))
			[i.start() for i in threads2]
			[i.join() for i in threads2]
			return self._sources
		except:
			source_utils.scraper_error('1337X')
			return self._sources


	def _get_items(self, url):
		try:
			headers = {'User-Agent': client.agent()}
			r = client.request(url, headers=headers)
			if '<tbody' not in r: return self.items
			posts = client.parseDOM(r, 'tbody')[0]
			posts = client.parseDOM(posts, 'tr')

			for post in posts:
				data = client.parseDOM(post, 'a', ret='href')[1]
				link = urljoin(self.base_link, data)

				name = client.parseDOM(post, 'a')[1]
				name = source_utils.clean_name(unquote_plus(name))
				if not source_utils.check_title(self.title, self.aliases, name, self.hdlr, self.year):
					continue
				name_info = source_utils.info_from_name(name, self.title, self.year, self.hdlr, self.episode_title)
				if source_utils.remove_lang(name_info): continue

				if not self.episode_title: #filter for eps returned in movie query (rare but movie and show exists for Run in 2020)
					ep_strings = [r'(?:\.|\-)s\d{2}e\d{2}(?:\.|\-|$)', r'(?:\.|\-)s\d{2}(?:\.|\-|$)', r'(?:\.|\-)season(?:\.|\-)\d{1,2}(?:\.|\-|$)']
					if any(re.search(item, name.lower()) for item in ep_strings): continue

				try:
					seeders = int(client.parseDOM(post, 'td', attrs={'class': 'coll-2 seeds'})[0].replace(',', ''))
					if self.min_seeders > seeders: continue
				except:
					seeders = 0

				try:
					size = re.findall('((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GiB|MiB|GB|MB))', post)[0]
					dsize, isize = source_utils._size(size)
				except:
					isize = '0'
					dsize = 0

				self.items.append((name, name_info, link, isize, dsize, seeders))
			return self.items
		except:
			source_utils.scraper_error('1337X')
			return self.items


	def _get_sources(self, item):
		try:
			quality, info = source_utils.get_release_quality(item[1], item[2])
			if item[3] != '0':
				info.insert(0, item[3])
			info = ' | '.join(info)

			data = client.request(item[2])
			data = client.parseDOM(data, 'a', ret='href')

			url = [i for i in data if 'magnet:' in i][0]
			url = unquote_plus(url).replace('&amp;', '&').replace(' ', '.').split('&tr')[0]
			url = source_utils.strip_non_ascii_and_unprintable(url)
			hash = re.compile('btih:(.*?)&').findall(url)[0]

			self._sources.append({'provider': '1337x', 'source': 'torrent', 'seeders': item[5], 'hash': hash, 'name': item[0], 'name_info': item[1], 'quality': quality,
												'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': item[4]})
		except:
			source_utils.scraper_error('1337X')


	def resolve(self, url):
		return url