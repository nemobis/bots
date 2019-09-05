#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Script to process the TNTvillage dump and mirror the items
on the Internet Archive (archive.org).

Usage:
    ia-tntvillage.py --help
    ia-tntvillage.py <tnt_dump>

Options:
    --help             Prints this documentation.
    <tnt_dump>         The CSV dump to read from.
    
The expected dump format is:

DATA: data in formato ISO 8601
HASH: info_hash codicato in esadecimale
TOPIC: ID numerico relativo alla discussione (forum TNTVillage)
POST: ID numerico relativo al messaggio (forum TNTVillage)
AUTORE: nome utente dell'autore della release
TITOLO: titolo della release
DESCRIZIONE: metadati relativi alla release
DIMENSIONE: dimensione complessiva dei file della release (in byte)
CATEGORIA: ID numerico relativo alla categoria della release

List the unfinished torrents:
https://archive.org/metamgr.php?w_identifier=tntvillage*&w_subject=TNTvillage*&w_size=%3C10000

Group by contributor:
https://archive.org/metamgr.php?f=histogram&group=contributor&w_identifier=tntvillage*&w_subject=TNTvillage*&w_size=%3C10000
    
"""
#
# (C) Federico Leva, 2019
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'

import csv
from collections import namedtuple
import docopt
from internetarchive import get_item, upload
from kitchen.text.converters import to_unicode
from lxml import html, etree
import os
import re
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
try:
	from StringIO import StringIO
except ImportError:
	from io import StringIO
from time import sleep
import sys
import threading

session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 502, 503, 504 ])
session.mount('https://', HTTPAdapter(max_retries=retries))

class Release:
	def __init__(self, release):
		self.tntid = release.TOPIC
		self.infohash = release.HASH
		self.contributor = release.AUTORE
		self.releasedate = release.DATA
		self.description = release.DESCRIZIONE + '\n' + str(self.getdescription(release.TOPIC))
		self.title = release.TITOLO
		self.date = self.getyear(release.TITOLO, self.description)
		self.language = self.getlanguage(release.DESCRIZIONE)
		self.collection, self.mediatype = self.gettype(release.CATEGORIA)
		self.subjects = self.getsubjects(release.CATEGORIA, release.DESCRIZIONE)
	
	def getlanguage(self, description):
		# TODO: Add languages? Italian is 84 % and the next 3 bring it to 87 %.
		languages = re.findall(r"\b(ita|eng|fra|jap)\b", description, flags=re.I)
		if languages is not None:
			return languages[0]

	def getyear(self, title, description):
		# FIXME things not to much
		# Editore: Mondadori - Urania n. 1469
		try:
			year = re.search(r'\b(19|20)[0-9]{2}\b', title)
			if year:
				year = year.group(0)
				return year
			if not year:
				years = re.findall(r'\b(?:Anno|Data|Editore|Edizione|Released?|Uscita|Collana|Titolo)\b[^{&]{0,30}\b([0-9]{4}\b)', description, flags=re.S)
				print(years)
			if years:
				return years[0]
		except Exception as e:
			print(e)
			return

	def getdescription(self, postid):
		tnt = session.get("https://web.archive.org/web/20190831000000/http://forum.tntvillage.scambioetico.org/index.php?showtopic={}".format(self.tntid))
		topic = html.fromstring(tnt.text)
		# Pick whichever post content comes first
		try:
			description = etree.tostring(topic.xpath('//table//td[contains(@class,"post2")]')[1]).decode("utf-8", "replace")
		except:
			description = topic
		return description

	def gettype(self, category):
		category = int(category)
		if category in [1, 4, 7, 8, 14, 22, 29]:
			return "opensource_movies", "movies"
		if category in [6, 9, 10, 11, 26, 28]:
			return "open_source_software", "software"
		if category in [2, 21, 35]:
			return "opensource_audio", "audio"
		if category in [3, 30, 34, 36]:
			return "opensource", "texts"
		if category in [27]:
			return "opensource_image", "image"
		return "opensource_media", "data"

	def getsubjects(self, category, description):
		# Subjects as in the original
		subjects = {
			1: "Film TV e programmi",
			2: "Musica",
			3: "E Books",
			4: "Film",
			6: "Linux",
			7: "Anime",
			8: "Cartoni",
			9: "Macintosh",
			10: "Windows software",
			11: "PC game",
			12: "Playstation",
			13: "Students releases",
			14: "Documentari",
			21: "Video musicali",
			22: "Sport",
			23: "Teatro",
			24: "Wrestling",
			25: "Varie",
			26: "Xbox",
			27: "Immagini sfondi",
			28: "Altri giochi",
			29: "Serie TV",
			30: "Fumetteria",
			31: "Trash",
			32: "Nintendo",
			34: "E-book",
			35: "Podcast",
			36: "Edicola",
			37: "Mobile",
		}
		additionalsubjects = {
			1: "TV",
			2: "music",
			3: "ebooks",
			4: "movies",
			8: "cartoons",
			11: "videogames",
			12: "videogames",
			13: "education",
			14: "documentaries",
			21: "music",
			23: "theatre",
			24: "sport",
			26: "videogames",
			28: "videogames",
			29: "TV series",
			30: "comics",
			32: "videogames",
			34: "ebooks",
			36: "magazines",
		}
		iasubjects = [ "TNTvillage",
			subjects[int(category)],
			"TNT-{}".format(category) ]
		if int(category) in additionalsubjects.keys():
			iasubjects.append(additionalsubjects[int(category)])
		descsubjects = set(re.split(r' *(?: \- |\[|\]) *', description))
		descsubjects = [s for s in descsubjects if s is not ""]
		return "; ".join(iasubjects + descsubjects)

	def iseligible(self):
		# Check suitable date
		if self.date and int(self.date) > 2000:
			print("Date too recent for {}: {}".format(self.tntid, self.date))
			return False

		# Get a description for the hash from trackers
		torrentz = session.get("https://torrentz2.eu/{}".format(self.infohash.lower()))
		# Look for rows which contain numbers of nodes
		noderows = html.fromstring(torrentz.text).xpath('//dd//span/text()')
		# Exclude "24 hours" and the like
		nodecounts = set([int(i) for i in noderows if ' ' not in i])
		if 0 in nodecounts:
			nodecounts.remove(0)
		# If there is a number of nodes other than 0, torrent may be active
		if nodecounts and len(nodecounts) >= 1:
			print("Found nodes for {}".format(self.infohash))
			return True

		# Unknown torrent may be removed due to takedowns or other reasons
		print("{} was not found or has no connected nodes".format(self.infohash))
		return None

	def upload(self):
		md = {
			"collection": self.collection,
			"licenseurl": "https://rightsstatements.org/vocab/CNE/1.0/",
			"mediatype": self.mediatype,
			"subject": self.subjects,
			"external-identifier": "urn:tntvillage:{}".format(self.tntid),
			"originalurl": "https://web.archive.org/web/20190831000000/http://forum.tntvillage.scambioetico.org/index.php?showtopic={}".format(self.tntid),
			"contributor": self.contributor,
			"last-updated-date": self.releasedate,
			"date": self.date,
			"description": self.description,
			"language": self.language,
			"title": self.title,
		}
		#print(md)

		identifier = 'tntvillage_{}'.format(self.tntid)
		torrentname = "/tmp/{}.torrent".format(identifier)
		torrentdesc = "/tmp/{}.html".format(identifier)
		with open(torrentname, 'w') as torrentfile:
			torrentfile.write('magnet:?xt=urn:btih:{}&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969%2Fannounce&tr=http%3A%2F%2Ftracker.tntvillage.scambioetico.org%3A2710%2Fannounce&tr=udp%3A%2F%2Ftracker.pirateparty.gr%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.internetwarriors.net%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.leechers-paradise.org%3A6969%2Fannounce'.format(self.infohash))
		with open(torrentdesc, 'w') as torrentdescfile:
			torrentdescfile.write(self.description)
		r = upload(identifier, files=[torrentname, torrentdesc], metadata=md)
		os.remove(torrentname)
		os.remove(torrentdesc)
		if r[0].status_code < 400:
			return True

def worker(release=None):
	try:
		item = Release(release)
		item.upload()
	except:
		sleep(180)

def isiaduplicate(topic):
	iaid = "tntvillage_{}".format(topic)

	iaitem = get_item(iaid)
	if iaitem.item_size:
		print("Skipping, {} already exists".format(iaid))
		return True

def main(argv=None):
	args = docopt.docopt(__doc__, argv=argv)

	with open(args['<tnt_dump>'], 'r', encoding='utf-8') as dump:
		source = csv.reader(dump, delimiter=',')
		header = next(source)
		releases = namedtuple('releases', ', '.join(header))
		releases = [releases._make(row) for row in source]

	for release in releases:
		print(release)
		if isiaduplicate(release.TOPIC):
			continue
		#threading.Thread(target=worker, args=[release]).start()
		try:
			item = Release(release)
			if not item.iseligible():
				print("Skipping {}".format(release.HASH))
				continue
			upload = item.upload()
			if upload:
				print("Upload successful for release {}".format(release.TOPIC))
		except Exception as e:
			print("ERROR: unexpected error uploading")
			print(e)
			sleep(180)
		sleep(10)

if __name__ == '__main__':
	main()
