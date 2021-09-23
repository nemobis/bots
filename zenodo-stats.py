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
__version__ = '0.2.1'
from datetime import datetime
import requests
from time import sleep
from urllib.parse import quote_plus

class ZenodoStats:
	def __init__(self, batchdays=10):
		self.views = 0
		self.downloads = 0
		self.items = 0
		self.recids = set()
		self.batchdays = batchdays
	
	def get_records(self, day):
		if not day % self.batchdays == 0:
			return []

		# Request a sufficiently small range to remain under 10k records
		datefrom = datetime.fromordinal(day).isoformat()[:10]
		dateto = datetime.fromordinal(day+self.batchdays-1).isoformat()[:10]
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

				# We can make maximum 60 API requests per minute
				sleep(1)

			return records
		except ValueError:
			sleep(10)
		except AttributeError:
			sleep(10)
		except requests.exceptions.RequestException:
			sleep(60)
	#	except Exception:
	#		# TODO: Check for connection issues vs. throttling
	#		sleep(60)
	#		continue
		finally:
			return records

	def add_record_counts(self, records=[], print_progress=True):
		for record in records:
			record = self.filter_record(record)

			recid = record.get("conceptrecid", None)
			if recid in self.recids:
				# We already counted it
				continue
			else:
				self.recids.add(recid)

			stats = record.get("stats", None)
			if not stats or not stats.get("downloads", None):
				continue
			self.items += 1
			if print_progress:
				if self.items % 100 == 0:
					print(".", end="", flush=True)
				if self.items % 1000 == 0:
					print("{}k".format(int(self.items / 1000)), end="", flush=True)
			self.downloads += stats.get('unique_downloads', 0)
			self.views += stats.get('version_unique_views', 0)

	# Default no-op filter, designed to be overridden
	def filter_record(self, record={}):
		return record

	def print_totals(self):
		if self.items == 0:
			print("No items found, nothing to report")
			return

		print("\n{} items got {} views and {} downloads, summing to a mean of {} each"
		.format(self.items,
				self.views,
				self.downloads,
				(int(self.views)+int(self.downloads))/self.items
				)
		)

class DisseminStats(ZenodoStats):
	def filter_record(self, record={}):
		if 13380 in record.get("owners", []):
			return record
		else:
			return {}

def main():
	zenodo = ZenodoStats()
	dissemin = DisseminStats()
	today = datetime.today().toordinal()
	minday = datetime(2021, 1, 1).toordinal()

	for day in range(minday, today):
		records = zenodo.get_records(day)
		zenodo.add_record_counts(records)
		# Only count uploads via Dissem.in
		dissemin.add_record_counts(records, print_progress=False)

	zenodo.print_totals()
	print("As for Dissemin uploads:")
	dissemin.print_totals()

if __name__ == "__main__":
    main()
