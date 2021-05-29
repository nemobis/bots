#!/usr/bin/python
# -*- coding: utf-8  -*-
""" Bot to scrape a list of book offerings from ISBN """
#
# (C) Federico Leva, 2018
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.2'

import requests
try:
    from isbnlib import is_isbn10, is_isbn13, isbn_from_words
except ImportError:
    print("WARNING: No isbnlib, cannot query ISBNS")
from lxml import html
import re
from time import sleep
try:
	import unicodecsv as csv
except ImportError:
	import csv
s = requests.Session()
t = requests.Session()
#headers = {'user-agent': '', 'cookie': ''}

def getAbebooks(isbn, fulltitle=None, keywords=None):
	notes = ''
	year = ''

	if isbn:
		url = 'https://www.abebooks.it/servlet/SearchResults?isbn={}&sortby=2'.format(isbn)
	elif fulltitle:
		url = 'https://www.abebooks.it/servlet/SearchResults?an={}&pn={}&tn={}&yrl={}&sortby=2'.format(
			fulltitle['authors'], fulltitle['publisher'], fulltitle['title'], fulltitle['year'])
		year = fulltitle['year']
	elif keywords:
		url = 'https://www.abebooks.it/servlet/SearchResults?kn={}&sortby=2'.format(keywords)
	else:
		return
	r = t.get(url, timeout=10, headers=headers).text

	listing = html.fromstring( r )
	price = listing.xpath('//div[@id="srp-item-price-1"]/text()')[0]
	seller = listing.xpath('//a[text()="Informazioni sul venditore"]/@href')[0] or ''
	title = listing.xpath('//li[@id="book-1"]//h2[@itemprop="offers"]/a[@itemprop="url"]/span/text()')[0] or ''
	description = listing.xpath('//li[@id="book-1"]//p[contains(@class, "p-md-t")]/span[contains(.," 19") or contains(.," 20")]/text()') or ''

	if not isbn:
		isbn = listing.xpath('//li[@id="book-1"]//p[contains(@class, "isbn")]//a/@title')[-1]
	if description:
		year = re.findall(r'\b(?:19|20)[0-9]{2}\b', description[0])[0]
	if 'Anybook' in seller:
		notes = listing.xpath('//li[@id="book-1"]//p[contains(@class, "p-md-t")]/text()')[0].strip().replace('Codice articolo ', '')
	return [isbn, seller, price, title, year, notes]

def getAlibris(isbn):
	sleep(4)
	alibris = t.get('https://www.alibris.com/search/books/isbn/%s' % isbn , timeout=10).text
	if 'Enter Your Search Terms' in alibris:
		return
	listing = html.fromstring(alibris)
	price = listing.xpath('//td[@class="price"]/p/text()')[0]
	#seller = listing.xpath('//td[@class="seller"]//a[@class="seller-link"]/text()')[0]
	#title = listing.xpath('//h1/[@itemprop="name"]/text()')
	#description = listing.xpath('//p[@id="synopsis-limited"]/text()')
	#year = listing.xpath('//span[@itemprop="datePublished"]/text()')
	return [isbn, '', price.strip(), '', '', '']

def getLibraccio(isbn):
	listing = html.fromstring( s.get('http://libraccio.it/libro/%s/' % isbn).text )
	price = listing.xpath('//span[@class="currentprice" and @id="C_C_ProductDetail_lSellPriceU"]/text()')[0]
	return [isbn, u'Libraccio', price, u'']

def parseItalianCitation(wikitext):
	# Simplistic parser to get just some data
	# TODO: https://github.com/dissemin/wikiciteparser/issues/2
	try:
		citation = {
			'title': ' '.join(re.findall('titolo *= *([^|}]+)', wikitext, flags=re.I)),
			'authors': ' '.join(re.findall('(?:nome|cognome|autore|curatore) *= *([^|}]+)', wikitext, flags=re.I)),
			'publisher': ' '.join(re.findall('editore *= *([^|}]+)', wikitext, flags=re.I)),
			'year': ''.join(re.findall('anno *= *([^|}]+)', wikitext, flags=re.I)).strip(),
		}
		if len(''.join(citation.values())) > 10:
			return citation
		else:
			return False
	except IndexError:
		return None

def main():
	wishlist = open('wishlist.txt', 'r')
	offerings = open('wishlist-offerings.csv', 'a')

	writer = csv.writer(offerings,
			delimiter='\t',
			lineterminator='\n',
			quoting=csv.QUOTE_MINIMAL,
			)
	writer.writerow([u'ISBN', u'Bookshop', u'Price', u'Title', u'Year', 'Notes'])

	for code in wishlist.readlines():
		code = code.strip()
		keywords = None
		if is_isbn10(code) or is_isbn13(code):
			isbn = code
			fulltitle = None
		else:
			isbn = None
			fulltitle = parseItalianCitation(re.sub('[[\]]', '', code))
			print(fulltitle)
			keywords = ' '.join(re.findall('\| *(?:\w+ *= *)?([^|}]+)', re.sub('[\[\]]', '', code)))
			if not fulltitle:
				print(keywords)

		try:
			offer = getAbebooks(isbn, fulltitle, keywords)
			if keywords and not offer:
				offer = getAbebooks(None, None, keywords)
			if offer:
				writer.writerow(offer)
				print("INFO: Found {}".format(offer[0]))
			else:
				print("NOTICE: Not found: {}".format(isbn))
			sleep(0.1)
		except IndexError as e:
			print("NOTICE: Not found: {}".format(isbn))
		except requests.exceptions.ConnectionError:
			print("WARNING: Connection error. Sleeping.")
			sleep(5)
		except requests.exceptions.ReadTimeout:
			print("WARNING: Connection timeout. Sleeping.")
			sleep(15)
		except Exception as e:
			print("ERROR: Unexpected exception")
			print(e)
			sleep(30)
			pass

	wishlist.close()
	offerings.close()

if __name__ == "__main__":
	main()
