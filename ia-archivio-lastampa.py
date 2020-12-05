#!/usr/bin/python3
# -*- coding: utf-8  -*-
""" Bot to download archiviolastampa.it """
#
# (C) Federico Leva, 2020
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'

import datetime
import json
import os
import re
import requests
from time import sleep

def getDayId(day, headboard='01'):
	"""
	Get the magic ID of the day from the index of the next day.
	Takes day in datetime format and issue type (01 or 02) as string.
	"""

	next_day = (day + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
	url = "http://www.archiviolastampa.it/index2.php?option=com_lastampa&task=issue&no_html=1&type=neighbors&headboard={}&date={}%2000:00:00".format(headboard, next_day)
	index = requests.get(url)

	# Expected output is something like:
	# {"previousIssueId":"1319_02_1989_0242_0001","nextIssueId":"1319_02_1989_0244_0001"} 
	if index.status_code < 300:
		return index.json()['previousIssueId']

def getIssueMetadata(identifier):
	""" Issue metadata from the identifier """

	url = "http://www.archiviolastampa.it/index2.php?option=com_lastampa&task=issue&no_html=1&type=info&issueid={}".format(identifier)
	info = requests.get(url)

	# Expected output is something like:
	# {"id_testata":"02","uscita":"243","data_uscita":"1989-09-13 00:00:00","nome_testata":"Europa"} 
	if info.status_code < 300:
		return info.json()

def makeDay(day, metadata):
	""" Prepare the download of this day, if appropriate """

	day_ymd = day.strftime('%Y-%m-%d')
	if day_ymd in metadata['data_uscita']:
		try:
			os.mkdir(day_ymd)
		except FileExistsError:
			print("INFO: Day {} was already done".format(day_ymd))
			return False

		with open('{}/issue_metadata.json'.format(day_ymd), 'w') as jsonout:
			jsonout.write(json.dumps(metadata))
		return True
	else:
		# We got a different day, probably there's a gap for festivities.
		return False

def downloadDay(day):
	""" Retrieve data for issue, prepare files and download images """

	day_ymd = day.strftime('%Y-%m-%d')
	incomplete = None
	identifier = getDayId(day)
	print("INFO: Found {} for {}".format(identifier, day.strftime('%Y-%m-%d')))
	metadata = getIssueMetadata(identifier)
	sleep(0.1)
	if not metadata:
		print("WARNING: could not download metadata for {}".format(day_ymd))
		return False

	if not makeDay(day, metadata):
		# We got a different day, probably there's a gap for festivities.
		return None

	# Prepare a session for this issue
	s = requests.Session()
	# We need the parameter from the hidden input
	# <input type="hidden" name="t" value="a2016dedff5843c652d2fdf4f87055cc" />
	home = s.get('http://www.archiviolastampa.it/')
	t = re.findall('<input type="hidden" name="t" value="([a-z0-9]+)"', home.text)[0]
	sleep(0.1)

	# List pages in the issue
	pages = s.get('http://www.archiviolastampa.it/load.php?url=/item/getPagesInfo.do?id={}&s={}'.format(identifier, t))
	with open('{}/{}_pages.json'.format(day_ymd, identifier), 'w') as pages_out:
		pages_out.write(pages.text)
	sleep(0.1)

	for page in pages.json()['pageList']:
		page_id = page['thumbnailId']
		page_image = s.get('http://www.archiviolastampa.it/load.php?url=/downloadContent.do?id={}_19344595&s={}'.format(page_id, t))
		sleep(0.2)
		if not 'image/jpeg' in page_image.headers['Content-Type']:
			print("WARNING: could not download an image for {}".format(page_id))
			incomplete = True
			sleep(5)
			continue
		with open('{}/{}.jpg'.format(day_ymd, page_id), 'wb') as page_out:
			page_out.write(page_image.content)

		page_data = s.get('http://www.archiviolastampa.it/load.php?url=/search/select/?wt=json&q=pageID:{}&s={}&s={}'.format(page_id, t, t))
		with open('{}/{}_pagedata.json'.format(day_ymd, page_id), 'w') as page_meta:
			page_meta.write(page_data.text)
		sleep(0.1)

	if incomplete:
		return False
	return True

def listDates(start, end):
	""" Return list of days between two dates """

	first_day = datetime.datetime.strptime(start, '%Y-%m-%d')
	last_day = datetime.datetime.strptime(end, '%Y-%m-%d')
	return [first_day + datetime.timedelta(days=x) for x in range(0, (last_day-first_day).days)]

def main():
	retry = open('retry.log', 'a')
	for day in listDates('1868-01-01', '2005-12-31'):
		try:
			download = downloadDay(day)
			sleep(2)
		except Exception as e:
			print(e)
			download = False
		if download is None:
			print("INFO: Nothing to do for {}".format(day))
			continue
		if download is False:
			print("ERROR: Something went wrong with {}, please retry. Sleeping now.".format(day))
			retry.write("{}\n".format(day))
			sleep(30)
			
	retry.close()
if __name__ == "__main__":
	main()