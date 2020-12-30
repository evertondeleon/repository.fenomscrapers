# -*- coding: utf-8 -*-
# created by Venom for Fenomscrapers (updated 12-23-2020)
'''
	Fenomscrapers Project
'''

import re

try: from urlparse import parse_qs, urljoin
except ImportError: from urllib.parse import parse_qs, urljoin
try: from urllib import urlencode, quote_plus, unquote_plus
except ImportError: from urllib.parse import urlencode, quote_plus, unquote_plus

from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils
from fenomscrapers.modules import workers


class source:
	def __init__(self):
		self.priority = 2
		self.language = ['en']
		self.domains = ['idope.se, idope.today']
		self.base_link = 'http://idope.se'
		self.search_link = '/torrent-list/%s/'
		self.min_seeders = 1
		self.pack_capable = True


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
		self.sources = []
		if not url: return self.sources
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
			url = self.search_link % quote_plus(query)
			url = urljoin(self.base_link, url)
			urls.append(url)
			urls.append(url + '?p=2')
			# log_utils.log('urls = %s' % urls, log_utils.LOGDEBUG)

			threads = []
			for url in urls:
				threads.append(workers.Thread(self.get_sources, url))
			[i.start() for i in threads]
			[i.join() for i in threads]
			return self.sources
		except:
			source_utils.scraper_error('IDOPE')
			return self.sources


	def get_sources(self, url):
		try:
			r = client.request(url)
			if not r: return
			div = client.parseDOM(r, 'div', attrs={'id': 'div2child'})

			for row in div:
				row = client.parseDOM(r, 'div', attrs={'class': 'resultdivbotton'})
				if not row: return

				for post in row:
					hash = re.findall('<div id="hideinfohash.+?" class="hideinfohash">(.+?)<', post, re.DOTALL)[0]
					name = re.findall('<div id="hidename.+?" class="hideinfohash">(.+?)<', post, re.DOTALL)[0]
					name = unquote_plus(name)
					name = source_utils.clean_name(name)
					if not source_utils.check_title(self.title, self.aliases, name, self.hdlr, self.year): continue
					name_info = source_utils.info_from_name(name, self.title, self.year, self.hdlr, self.episode_title)
					if source_utils.remove_lang(name_info): continue

					url = 'magnet:?xt=urn:btih:%s&dn=%s' % (hash, name)
					if url in str(self.sources): continue

					if not self.episode_title: #filter for eps returned in movie query (rare but movie and show exists for Run in 2020)
						ep_strings = [r'(?:\.|\-)s\d{2}e\d{2}(?:\.|\-|$)', r'(?:\.|\-)s\d{2}(?:\.|\-|$)', r'(?:\.|\-)season(?:\.|\-)\d{1,2}(?:\.|\-|$)']
						if any(re.search(item, name.lower()) for item in ep_strings): continue

					try:
						seeders = int(re.findall('<div class="resultdivbottonseed">([0-9]+|[0-9]+,[0-9]+)<', post, re.DOTALL)[0].replace(',', ''))
						if self.min_seeders > seeders: continue
					except:
						seeders = 0

					quality, info = source_utils.get_release_quality(name_info, url)
					try:
						size = re.findall('<div class="resultdivbottonlength">(.+?)<', post)[0]
						dsize, isize = source_utils._size(size)
						info.insert(0, isize)
					except:
						dsize = 0
					info = ' | '.join(info)

					self.sources.append({'provider': 'idope', 'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'name_info': name_info, 'quality': quality,
													'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
		except:
			source_utils.scraper_error('IDOPE')


	def sources_packs(self, url, hostDict, search_series=False, total_seasons=None, bypass_filter=False):
		self.sources = []
		if not url: return self.sources
		try:
			self.search_series = search_series
			self.total_seasons = total_seasons
			self.bypass_filter = bypass_filter

			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			self.title = data['tvshowtitle'].replace('&', 'and').replace('Special Victims Unit', 'SVU')
			self.aliases = data['aliases']
			self.imdb = data['imdb']
			self.year = data['year']
			self.season_x = data['season']
			self.season_xx = self.season_x.zfill(2)

			query = re.sub('[^A-Za-z0-9\s\.-]+', '', self.title)
			queries = [
						self.search_link % quote_plus(query + ' S%s' % self.season_xx),
						self.search_link % quote_plus(query + ' Season %s' % self.season_x)
							]
			if search_series:
				queries = [
						self.search_link % quote_plus(query + ' Season'),
						self.search_link % quote_plus(query + ' Complete')
								]

			threads = []
			for url in queries:
				link = urljoin(self.base_link, url)
				threads.append(workers.Thread(self.get_sources_packs, link))
			[i.start() for i in threads]
			[i.join() for i in threads]
			return self.sources
		except:
			source_utils.scraper_error('IDOPE')
			return self.sources


	def get_sources_packs(self, link):
		# log_utils.log('link = %s' % str(link), __name__, log_utils.LOGDEBUG)
		try:
			r = client.request(link)
			if not r: return
			div = client.parseDOM(r, 'div', attrs={'id': 'div2child'})

			for row in div:
				row = client.parseDOM(r, 'div', attrs={'class': 'resultdivbotton'})
				if not row: return

				for post in row:
					hash = re.findall('<div id="hideinfohash.+?" class="hideinfohash">(.+?)<', post, re.DOTALL)[0]
					name = re.findall('<div id="hidename.+?" class="hideinfohash">(.+?)<', post, re.DOTALL)[0]
					name = unquote_plus(name)
					name = source_utils.clean_name(name)

					url = 'magnet:?xt=urn:btih:%s&dn=%s' % (hash, name)
					if url in str(self.sources): continue

					if not self.search_series:
						if not self.bypass_filter:
							if not source_utils.filter_season_pack(self.title, self.aliases, self.year, self.season_x, name):
								continue
						package = 'season'

					elif self.search_series:
						if not self.bypass_filter:
							valid, last_season = source_utils.filter_show_pack(self.title, self.aliases, self.imdb, self.year, self.season_x, name, self.total_seasons)
							if not valid: continue
						else:
							last_season = self.total_seasons
						package = 'show'

					name_info = source_utils.info_from_name(name, self.title, self.year, season=self.season_x, pack=package)
					if source_utils.remove_lang(name_info): continue

					try:
						seeders = int(re.findall('<div class="resultdivbottonseed">([0-9]+|[0-9]+,[0-9]+)<', post, re.DOTALL)[0].replace(',', ''))
						if self.min_seeders > seeders: continue
					except:
						seeders = 0

					quality, info = source_utils.get_release_quality(name_info, url)
					try:
						size = re.findall('<div class="resultdivbottonlength">(.+?)<', post)[0]
						dsize, isize = source_utils._size(size)
						info.insert(0, isize)
					except:
						dsize = 0
					info = ' | '.join(info)

					item = {'provider': 'idope', 'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'name_info': name_info, 'quality': quality,
								'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize, 'package': package}
					if self.search_series:
						item.update({'last_season': last_season})
					self.sources.append(item)
		except:
			source_utils.scraper_error('IDOPE')


	def resolve(self, url):
		return url