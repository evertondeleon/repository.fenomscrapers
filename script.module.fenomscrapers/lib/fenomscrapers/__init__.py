# -*- coding: UTF-8 -*-

import os.path
import pkgutil
from fenomscrapers.modules import log_utils
try:
	import xbmcaddon
	__addon__ = xbmcaddon.Addon(id='script.module.fenomscrapers')
except:
	__addon__ = None
debug = __addon__.getSetting('debug.enabled') == 'true'


def sources(specified_folders=None):
	try:
		sourceDict = []
		if __addon__: provider = __addon__.getSetting('module.provider')
		else: provider = 'fenomscrapers'
		sourceFolder = getScraperFolder(provider)
		sourceFolderLocation = os.path.join(os.path.dirname(__file__), sourceFolder)
		sourceSubFolders = [x[1] for x in os.walk(sourceFolderLocation)][0]
		if specified_folders:
			sourceSubFolders = specified_folders
		for i in sourceSubFolders:
			for loader, module_name, is_pkg in pkgutil.walk_packages([os.path.join(sourceFolderLocation, i)]):
				if is_pkg: continue
				if enabledCheck(module_name):
					try:
						module = loader.find_module(module_name).load_module(module_name)
						sourceDict.append((module_name, module.source()))
					except Exception as e:
						if debug:
							log_utils.log('Error: Loading module: "%s": %s' % (module_name, e), log_utils.LOGDEBUG)
		return sourceDict
	except:
		return []

def enabledCheck(module_name):
	if __addon__ is not None:
		if __addon__.getSetting('provider.' + module_name) == 'true':
			return True
		else: return False
	return True

# def pack_sources():
	# try:
		# pack_sources = []
		# for source in sources():
			# if getattr(source[1], 'pack_capable', False):
				# pack_sources.append(source[0])
	# except Exception as e:
		# if debug:
			# log_utils.log('Error: Returning Pack Sources: %s' % str(e), log_utils.LOGDEBUG)
		# pass
	# return pack_sources

def pack_sources():
	return ['bitlord', 'bt4g', 'btdb', 'btscene', 'extratorrent', 'idope', 'kickass2', 'limetorrents', 'magnetdl', 'piratebay',
				'solidtorrents', 'torrentapi', 'torrentdownload', 'torrentfunk', 'torrentgalaxy', 'torrentparadise',
				'torrentz2', 'yourbittorrent', 'zooqle']

def getScraperFolder(scraper_source):
	sourceSubFolders = [x[1] for x in os.walk(os.path.dirname(__file__))][0]
	return [i for i in sourceSubFolders if scraper_source.lower() in i.lower()][0]