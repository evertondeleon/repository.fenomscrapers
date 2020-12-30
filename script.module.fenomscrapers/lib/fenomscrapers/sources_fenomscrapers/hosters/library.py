# -*- coding: UTF-8 -*-
#  (updated 12-23-2020)
'''
	Fenomscrapers Project
'''

import json

try: from urlparse import parse_qs
except ImportError: from urllib.parse import parse_qs
try: from urllib import urlencode
except ImportError: from urllib.parse import urlencode

from fenomscrapers.modules import control
from fenomscrapers.modules import cleantitle
from fenomscrapers.modules import source_utils


class source:
	def __init__(self):
		self.priority = 35
		self.language = ['en', 'de', 'fr', 'ko', 'pl', 'pt', 'ru']
		self.domains = []


	def movie(self, imdb, title, aliases, year):
		try:
			return urlencode({'imdb': imdb, 'title': title,'year': year})
		except:
			source_utils.scraper_error('LIBRARY')
			return


	def tvshow(self, imdb, tvdb, tvshowtitle, aliases, year):
		try:
			return urlencode({'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year})
		except:
			source_utils.scraper_error('LIBRARY')
			return


	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if not url: return
			url = parse_qs(url)
			url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
			url.update({'premiered': premiered, 'season': season, 'episode': episode})
			return urlencode(url)
		except:
			source_utils.scraper_error('LIBRARY')
			return


	def sources(self, url, hostDict):
		sources = []
		if not url: return sources
		try:
			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			content_type = 'episode' if 'tvshowtitle' in data else 'movie'
			years = (data['year'], str(int(data['year'])+1), str(int(data['year'])-1))

			if content_type == 'movie':
				title = cleantitle.get_simple(data['title']).lower()
				ids = [data['imdb']]
				r = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties": ["imdbnumber", "title", "originaltitle", "file"]}, "id": 1}' % years)
				r = unicode(r, 'utf-8', errors='ignore')
				if 'movies' not in r: return sources
				r = json.loads(r)['result']['movies']
				r = [i for i in r if str(i['imdbnumber']) in ids or title in [cleantitle.get_simple(i['title']), cleantitle.get_simple(i['originaltitle'])]]
				try: r = [i for i in r if not i['file'].encode('utf-8').endswith('.strm')]
				except: r = [i for i in r if not i['file'].endswith('.strm')]
				if not r: return sources
				r = r[0]
				r = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovieDetails", "params": {"properties": ["streamdetails", "file"], "movieid": %s }, "id": 1}' % str(r['movieid']))
				r = unicode(r, 'utf-8', errors='ignore')
				r = json.loads(r)['result']['moviedetails']

			elif content_type == 'episode':
				title = cleantitle.get_simple(data['tvshowtitle']).lower()
				season, episode = data['season'], data['episode']
				r = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties": ["imdbnumber", "title"]}, "id": 1}' % years)
				r = unicode(r, 'utf-8', errors='ignore')
				if 'tvshows' not in r: return sources
				r = json.loads(r)['result']['tvshows']
				r = [i for i in r if title in (cleantitle.get_simple(i['title']).lower() if not ' (' in i['title'] else cleantitle.get_simple(i['title']).split(' (')[0])]
				if not r: return sources
				else: r = r[0]
				r = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"filter":{"and": [{"field": "season", "operator": "is", "value": "%s"}, {"field": "episode", "operator": "is", "value": "%s"}]}, "properties": ["file"], "tvshowid": %s }, "id": 1}' % (str(season), str(episode), str(r['tvshowid'])))
				r = unicode(r, 'utf-8', errors='ignore')
				r = json.loads(r)['result']['episodes']
				if not r: return sources
				try: r = [i for i in r if not i['file'].encode('utf-8').endswith('.strm')]
				except: r = [i for i in r if not i['file'].endswith('.strm')]
				if not r: return sources
				r = r[0]
				r = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodeDetails", "params": {"properties": ["streamdetails", "file"], "episodeid": %s }, "id": 1}' % str(r['episodeid']))
				r = unicode(r, 'utf-8', errors='ignore')
				r = json.loads(r)['result']['episodedetails']

			try: url = r['file'].encode('utf-8')
			except: url = r['file']

			try:
				quality = int(r['streamdetails']['video'][0]['width'])
			except:
				source_utils.scraper_error('LIBRARY')
				quality = -1

			if quality > 1920: quality = '4K'
			if quality >= 1920: quality = '1080p'
			if 1280 <= quality < 1900: quality = '720p'
			if quality < 1280: quality = 'SD'

			info = []
			try:
				f = control.openFile(url) ; s = f.size() ; f.close()
				dsize = float(s) / 1073741824
				isize = '%.2f GB' % dsize
				info.insert(0, isize)
			except:
				source_utils.scraper_error('LIBRARY')
				dsize = 0

			try:
				c = r['streamdetails']['video'][0]['codec']
				if c == 'avc1': c = 'h264'
				info.append(c)
			except:
				source_utils.scraper_error('LIBRARY')

			try:
				ac = r['streamdetails']['audio'][0]['codec']
				if ac == 'dca': ac = 'dts'
				if ac == 'dtshd_ma': ac = 'dts-hd ma'
				info.append(ac)
			except:
				source_utils.scraper_error('LIBRARY')

			try:
				ach = r['streamdetails']['audio'][0]['channels']
				if ach == 1: ach = 'mono'
				if ach == 2: ach = '2.0'
				if ach == 6: ach = '5.1'
				if ach == 8: ach = '7.1'
				info.append(ach)
			except:
				source_utils.scraper_error('LIBRARY')

			info = ' | '.join(info)
			try: info = info.encode('utf-8')
			except: pass

			sources.append({'provider': 'library', 'source': 'local', 'quality': quality, 'language': 'en', 'url': url, 'info': info,
										'local': True, 'direct': True, 'debridonly': False, 'size': dsize})
			return sources
		except:
			source_utils.scraper_error('LIBRARY')
			return sources


	def resolve(self, url):
		return url