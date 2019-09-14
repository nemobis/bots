#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Script to count usage of Zenodo records.
"""
#
# (C) Federico Leva, 2019
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'
import grequests
import random
from sickle import Sickle

views = 0
downloads = 0
items = 0
rs = []
oai = Sickle('https://zenodo.org/oai2d')
i = 0

identifiers = random.sample(range(1,3500000), 5000)
"""
# Get the list of all actual records
for record in oai.ListRecords(metadataPrefix='oai_dc', ignore_deleted=True):
	items += 1
	if items % 1000 == 0:
		print("Listed {} records so far".format(items))
	identifiers += record.header.identifier.replace("oai:zenodo.org:", "")
items = 0
"""

for identifier in identifiers:
	i +=1
	rs.append(grequests.get('http://zenodo.org/api/records/{}'.format(identifier),
						 headers={'Accept': 'application/vnd.zenodo.v1+json'}) )

	if i < 10:
		continue

	for response in grequests.map(rs, size=5):
		try:
			data = response.json()
			# Exclude uploads via Dissem.in
			#if 'owners' in data.keys() and 13380 not in data['owners']:
			#	continue
			if 'stats' in data.keys() and 'downloads' in data['stats'].keys():
				items += 1
				downloads += data['stats']['unique_downloads']
				views += data['stats']['version_unique_views']
		except ValueError:
			continue
		except AttributeError:
			continue
		finally:
			rs = []
			i = 0

print("{} items got {} views and {} downloads, summing to a mean of {} each"
	  .format(items, views, downloads, (int(views)+int(downloads))/items) )
