#!/usr/bin/python
# -*- coding: utf-8  -*-
""" Bot to read autors and DOIs from a Web of Science (WoS/WoK) publication record. """
#
# (C) Federico Leva, 2017
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'

from lxml import etree
import unicodecsv as csv
import os

doicsv = open('doi-authors.csv', 'w')
header = ['First name', 'Last name', 'email', 'DOI']
out = csv.writer(doicsv,
		delimiter='\t',
		lineterminator='\n',
		quoting=csv.QUOTE_MINIMAL)
out.writerow(header)

for xml in [ each for each in os.listdir('.') if each.endswith('.xml') ]:
	try:
		record = etree.parse(open(xml, 'r'))
		names = record.xpath('//summary/names//email_addr/..')
		for name in names:
			author = [ name.xpath('first_name/text()')[0].strip(),
				name.xpath('last_name/text()')[0].strip(),
				name.xpath('email_addr/text()')[0].strip(),
				record.xpath('//identifier[@type = "doi"]/@value')[0].strip() ]
			out.writerow(author)
	except:
		print("%s is not a valid XML file" % xml)
