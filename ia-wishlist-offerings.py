#!/usr/bin/python
# -*- coding: utf-8  -*-
""" Bot to scrape a list of book offerings from ISBN """
#
# (C) Federico Leva, 2018
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'

import requests
from lxml import html
import unicodecsv as csv

s = requests.Session()
t = requests.Session()
wishlist = open('wishlist.txt', 'rb')
offerings = open('wishlist-offerings.csv', 'w')

writer = csv.writer(offerings,
		delimiter=b',',
		lineterminator='\n',
		quoting=csv.QUOTE_MINIMAL,
		encoding='utf-8'
		)
writer.writerow([u'ISBN', u'Bookshop', u'Price', 'Notes'])

for code in wishlist.readlines():
	code = code.strip()
	try:
	#	listing = html.fromstring( s.get('http://libraccio.it/libro/%s/' % code ).text )
	#	price = listing.xpath('//span[@class="currentprice" and @id="C_C_ProductDetail_lSellPriceU"]/text()')[0]
	#	writer.writerow([code, u'Libraccio', price, u''])

		listing = html.fromstring( t.get('https://www.abebooks.it/servlet/SearchResults?isbn=%s&sortby=2' % code ).text )
		price = listing.xpath('//span[@class="price"]/text()')[0]
		seller = listing.xpath('//a[text()="Informazioni sul venditore"]/@href')[0]
		writer.writerow([code, u'AbeBooks', price, seller])
	except:
		pass

wishlist.close()
offerings.close()
