#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Script to count usage of Zenodo records.
"""
#
# (C) Federico Leva, 2019-2021
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.2.0'
from datetime import datetime
import requests
from time import sleep
from urllib.parse import quote_plus

views = 0
downloads = 0
items = 0
i = 0
recids = set()
today = datetime.today().toordinal()
minday = datetime(1990, 1, 1).toordinal()
batchdays = 10

for day in range(minday, today):
	# Request a sufficiently small range to remain under 10k records
	if not day % batchdays == 0:
		continue
	datefrom = datetime.fromordinal(day).isoformat()[:10]
	dateto = datetime.fromordinal(day+batchdays-1).isoformat()[:10]
	daterange = quote_plus("[{} TO {}]".format(datefrom, dateto))
	records = []
	try:
		nextrecords = 'https://zenodo.org/api/records/?q=publication_date:{}&size=1000&sort=-mostviewed'.format(daterange)
		while nextrecords:
			r = requests.get(
				nextrecords,
				headers={'Accept': 'application/vnd.zenodo.v1+json'},
				timeout=(20, 60)
			)
			records += r.json().get("hits", None).get("hits", None)
			nextrecords = r.json().get("links", None).get("next", None)
	except ValueError:
		sleep(10)
		continue
	except AttributeError:
		sleep(10)
		continue
	except requests.exceptions.RequestException:
		sleep(60)
		continue
#	except Exception:
#		# TODO: Check for connection issues vs. throttling
#		sleep(60)
#		continue

	for record in records:
		# Exclude uploads via Dissem.in
		#if 'owners' in data.keys() and 13380 not in data['owners']:
		#	continue

		recid = record.get("conceptrecid", None)
		if recid in recids:
			# We already counted it
			continue
		else:
			recids.add(recid)

		stats = record.get("stats", None)
		if not stats or not stats.get("downloads", None):
			continue
		items += 1
		if items % 100 == 0:
			print(".", end="", flush=True)
		if items % 1000 == 0:
			print("{}k".format(items / 1000), end="", flush=True)
		downloads += stats.get('unique_downloads', 0)
		views += stats.get('version_unique_views', 0)

	# We can make maximum 60 API requests per minute
	sleep(1)

print("\n{} items got {} views and {} downloads, summing to a mean of {} each"
	  .format(items, views, downloads, (int(views)+int(downloads))/items) )
