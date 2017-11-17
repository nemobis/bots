#!/usr/bin/python
# -*- coding: utf-8  -*-
""" Bot to read autors and DOIs from a Web of Science (WoS/WoK) publication record. """
#
# (C) Federico Leva, 2017
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.2.0'

from lxml import etree
import unicodecsv as csv
import os

doicsv = open('doi-authors.csv', 'w')
header = ['Full name', 'First name', 'Last name', 'Entity', 'DOI', 'Title', 'email']
out = csv.writer(doicsv,
		delimiter='\t',
		lineterminator='\n',
		quoting=csv.QUOTE_MINIMAL)
out.writerow(header)

for xml in [ each for each in os.listdir('.') if each.endswith('.xml') ]:
	try:
		record = etree.parse(open(xml, 'r'))
		if not record.xpath('/records/REC'):
			print u"Empty record"
			continue

		# Addresses can be in one or both of the following
		addresses = (record.xpath('//fullrecord_metadata/*[name()="reprint_addresses"]') + record.xpath('//fullrecord_metadata/*[name()="addresses"]'))[0]
		addresses_count = int(addresses.xpath('./@count')[0])
		
		# Fetch the names and email addresses from the summary,
		# then look elsewhere for details.
		names = record.xpath('//summary/names//name')
		org = None
		for name in names:
			if addresses_count == 1:
				# All names are from the same address/organization
				try:
					org = addresses.xpath('//organizations')[0]
				except IndexError:
					org = None
			elif not addresses_count == 0:
				# We have some addresses but need to match them
				# Each name can have one or both of these IDs
				try:
					author_id = int( name.xpath('./@dais_id')[0] )
					author_id_ng = 0
				except IndexError:
					author_id = 0
					try:
						author_id_ng = int( name.xpath('./@daisng_id')[0] )
					except IndexError:
						author_id_ng = 0

				try:
					# Look for the same author by its ID in the address list
					# address_number = int(addresses.xpath('//name[(@dais_id = %d or @daisng_id = %d) and @addr_no > 0]/@addr_no' % (author_id, author_id_ng) )[0])
					org = addresses.xpath('//address_spec[@addr_no = 1]/organizations')[0]
				except IndexError:
					print "Could not find org for author %d/%d in %s" % (author_id, author_id_ng, xml)
					org = None
			if org is not None:
				try:
					# Try to fetch the preferred/controlled name for the org/address
					org_name = (org.xpath('organization[@pref="Y"]/text()') + org.xpath('organization[1]/text()'))[0]
				except IndexError:
					org_name = ''
			else:
				org_name = ''

			# None of these fields is guaranteed to exist
			try:
				first_name = name.xpath('first_name/text()')[0].strip()
			except:
				first_name = ''
			try:
				last_name = name.xpath('last_name/text()')[0].strip()
			except:
				last_name = ''
			try:
				full_name = name.xpath('full_name/text()')[0].strip()
			except:
				full_name = ''

			author = [ full_name, first_name, last_name, org_name,
				record.xpath('//identifier[@type = "doi" or @type = "xref_doi"]/@value')[0].strip(),
				record.xpath('//title[@type = "item"]/text()')[0].strip() ]

			if name.xpath('email_addr'):
				author.append( name.xpath('email_addr/text()')[0].strip() )
			out.writerow(author)

	except (etree.ElementTree, etree.XMLSyntaxError):
		print("%s is not a valid XML file" % xml)
