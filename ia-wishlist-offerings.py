#!/usr/bin/python
# -*- coding: utf-8  -*-
""" Bot to scrape a list of book offerings from ISBN """
#
# (C) Federico Leva, 2018
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.1'

import requests
from lxml import html
import re
from time import sleep
import unicodecsv as csv

s = requests.Session()
t = requests.Session()
wishlist = open('wishlist.txt', 'rb')
offerings = open('wishlist-offerings.csv', 'a')

writer = csv.writer(offerings,
		delimiter=b',',
		lineterminator='\n',
		quoting=csv.QUOTE_MINIMAL,
		encoding='utf-8'
		)
writer.writerow([u'ISBN', u'Bookshop', u'Price', u'Title', u'Year', 'Notes'])

for code in wishlist.readlines():
	code = code.strip()
	print code
	notes = ''
	year = ''
	try:
	#	listing = html.fromstring( s.get('http://libraccio.it/libro/%s/' % code ).text )
	#	price = listing.xpath('//span[@class="currentprice" and @id="C_C_ProductDetail_lSellPriceU"]/text()')[0]
	#	writer.writerow([code, u'Libraccio', price, u''])

		listing = html.fromstring( t.get('http://www.abebooks.it/servlet/SearchResults?isbn=%s&sortby=2' % code , timeout=10).text )
		price = listing.xpath('//div[@id="srp-item-price-1"]/text()')[0]
		seller = listing.xpath('//a[text()="Informazioni sul venditore"]/@href')[0]
		title = listing.xpath('//div[@id="book-1"]//h2/a[@itemprop="url"]/@title')[0]
		description = listing.xpath('//div[@id="book-1"]//p[contains(@class, "p-md-t")]/span[contains(.," 19") or contains(.," 20")]/text()')
		if description:
			year = re.findall(r'\b(?:19|20)[0-9]{2}\b', description[0])[0]
		if 'Anybook' in seller:
			notes = listing.xpath('//div[@id="book-1"]//p[contains(@class, "p-md-t")]/text()')[0].strip().replace('Codice articolo ', '')
		writer.writerow([code, seller, price, title, year, notes])
	except IndexError:
		print("NOTICE: not found")
	except requests.exceptions.ConnectionError:
		print("WARNING: Connection error. Sleeping.")
		sleep(5)
	except requests.exceptions.ReadTimeout:
		print("WARNING: Connection timeout. Sleeping.")
		sleep(15)
	except:
		print("ERROR: Unexpected exception")
		pass

wishlist.close()
offerings.close()
