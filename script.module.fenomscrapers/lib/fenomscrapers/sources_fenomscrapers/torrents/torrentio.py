# -*- coding: utf-8 -*-
# created by Venom for Fenomscrapers (11-28-2021)
'''
	Fenomscrapers Project
'''

from json import loads as jsloads
import re
from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils


class source:
	priority = 1
	pack_capable = True
	hasMovies = True
	hasEpisodes = True
	def __init__(self):
		self.language = ['en']
		self.domain = ['torrentio.strem.fun']
		self.base_link = 'https://torrentio.strem.fun'
		self.movieSearch_link = '/language=english/stream/movie/%s.json'
		self.tvSearch_link = '/language=english/stream/series/%s:%s:%s.json'
		self.min_seeders = 0

	def sources(self, data, hostDict):
		sources = []
		if not data: return sources
		append = sources.append
		try:
			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			title = title.replace('&', 'and').replace('Special Victims Unit', 'SVU')
			aliases = data['aliases']
			episode_title = data['title'] if 'tvshowtitle' in data else None
			year = data['year']
			hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else year
			imdb = data['imdb']

			if 'tvshowtitle' in data: url = '%s%s' % (self.base_link, self.tvSearch_link % (imdb, data['season'], data['episode']))
			else: url = '%s%s' % (self.base_link, self.movieSearch_link % imdb)
			# log_utils.log('url = %s' % url)

			rjson = client.request(url, timeout='5')
			if not rjson or rjson == 'null' or any(value in rjson for value in ('521 Origin Down', 'No results returned', 'Connection Time-out', 'Database maintenance')):
				return sources
			files = jsloads(rjson)['streams']
		except:
			source_utils.scraper_error('TORRENTIO')
			return sources
		for file in files:
			try:
				hash = file['infoHash']
				file_title = file['title'].split('\n')
				name = source_utils.clean_name(file_title[0])
				r = re.compile(r'👤.*')
				file_info = [x for x in file_title if r.match(x)][0]

				if not source_utils.check_title(title, aliases, name, hdlr, year): continue
				name_info = source_utils.info_from_name(name, title, year, hdlr, episode_title)
				if source_utils.remove_lang(name_info): continue

				url = 'magnet:?xt=urn:btih:%s&dn=%s' % (hash, name) 

				if not episode_title: #filter for eps returned in movie query (rare but movie and show exists for Run in 2020)
					ep_strings = [r'(?:\.|\-)s\d{2}e\d{2}(?:\.|\-|$)', r'(?:\.|\-)s\d{2}(?:\.|\-|$)', r'(?:\.|\-)season(?:\.|\-)\d{1,2}(?:\.|\-|$)']
					if any(re.search(item, name.lower()) for item in ep_strings): continue

				try:
					seeders = int(re.search(r'(\d+)', file_info).group(1))
					if self.min_seeders > seeders: continue
				except: seeders = 0

				quality, info = source_utils.get_release_quality(name_info, url)
				try:
					size = re.search(r'((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|Gb|MB|MiB|Mb))', file_info).group(0)
					dsize, isize = source_utils._size(size)
					info.insert(0, isize)
				except: dsize = 0
				info = ' | '.join(info)

				append({'provider': 'torrentio', 'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'name_info': name_info, 'quality': quality,
							'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
			except:
				source_utils.scraper_error('TORRENTIO')
		return sources

	def sources_packs(self, data, hostDict, search_series=False, total_seasons=None, bypass_filter=False):
		sources = []
		if not data: return sources
		sources_append = sources.append
		try:
			title = data['tvshowtitle'].replace('&', 'and').replace('Special Victims Unit', 'SVU')
			aliases = data['aliases']
			imdb = data['imdb']
			year = data['year']
			season = data['season']
			url = '%s%s' % (self.base_link, self.tvSearch_link % (imdb, data['season'], data['episode']))
			rjson = client.request(url, timeout='5')
			if not rjson or rjson == 'null' or any(value in rjson for value in ('521 Origin Down', 'No results returned', 'Connection Time-out', 'Database maintenance')):
				return sources
			files = jsloads(rjson)['streams']
		except:
			source_utils.scraper_error('TORRENTIO')
			return sources

		for file in files:
			try:
				hash = file['infoHash']
				file_title = file['title'].split('\n')
				name = source_utils.clean_name(file_title[0])
				r = re.compile(r'👤.*')
				file_info = [x for x in file_title if r.match(x)][0]
				if not search_series:
					if not bypass_filter:
						if not source_utils.filter_season_pack(title, aliases, year, season, name):
							continue
					package = 'season'

				elif search_series:
					if not bypass_filter:
						valid, last_season = source_utils.filter_show_pack(title, aliases, imdb, year, season, name, total_seasons)
						if not valid: continue
					else:
						last_season = total_seasons
					package = 'show'

				name_info = source_utils.info_from_name(name, title, year, season=season, pack=package)
				if source_utils.remove_lang(name_info): continue

				url = 'magnet:?xt=urn:btih:%s&dn=%s' % (hash, name)
				try:
					seeders = int(re.search(r'(\d+)', file_info).group(1))
					if self.min_seeders > seeders: continue
				except: seeders = 0

				quality, info = source_utils.get_release_quality(name_info, url)
				try:
					size = re.search(r'((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|Gb|MB|MiB|Mb))', file_info).group(0)
					dsize, isize = source_utils._size(size)
					info.insert(0, isize)
				except: dsize = 0
				info = ' | '.join(info)

				item = {'provider': 'torrentio', 'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'name_info': name_info, 'quality': quality,
							'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize, 'package': package}
				if search_series: item.update({'last_season': last_season})
				sources_append(item)
			except:
				source_utils.scraper_error('TORRENTIO')
		return sources

	def resolve(self, url):
		return url