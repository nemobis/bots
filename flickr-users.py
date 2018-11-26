#!/usr/bin/python
# -*- coding: utf-8  -*-
""" Script to find Flickr users exposed to deletions.
    https://blog.flickr.net/en/2018/11/07/the-commons-the-past-is-100-part-of-our-future/
"""
#
# (C) Federico Leva, 2018
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'
import sys
from time import sleep
import flickr_api
flickr_api.set_keys(api_key = 'xxxxxxxxxxxxxxxxxxxxxxxxx', api_secret = 'yyyyyyyyyyyyyy')

def doUser(url):
	user = flickr_api.Person.findByUrl(url)
	data = user.getInfo()
	if "ispro" in data.keys() and int(data['ispro']) > 0:
		pro = True
	else:
		pro = None
	count = data['photos_info']['count']
	if not pro and count > 1000:
		# https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.html
		countcc = flickr_api.Photo.search(user_id=user['id'], license="1,2,3,4,5,6").info.total
		photos = user.getPublicPhotos()
		if count > 0:
			lastdate = photos[0].getInfo()['taken']
		else:
			lastdate = ''
		if count-countcc > 1000:
			print u"{}\t{}\t{}\t{}".format(user['id'], lastdate, count, countcc)

if __name__ == "__main__":
	urls = open(sys.argv[1]).readlines()
	for url in urls:
		url = url.strip()
		try:
			doUser(url)
		except flickr_api.flickrerrors.FlickrError:
			sleep(10)
			continue
		except Exception as e:
			print(e)
			continue
