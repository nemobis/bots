#!/usr/bin/python
# -*- coding: utf-8  -*-
""" Bot to upload PDFs for a list of DOIs to the Internet Archive. """
#
# (C) Federico Leva, 2018
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'
from habanero import Crossref
from internetarchive import upload
try:
	from urllib import quote_plus
except:
	from urllib.parse import quote_plus
import re
from time import sleep

dois = open('dois.txt', 'r')
s = requests.Session()
cr = Crossref()
for doi in dois.readlines():
	doi = doi.strip()
	print("Looking up DOI: {}".format(doi))
	sleep(1)

	m = cr.works(doi=doi)['message']['items'][0]

	metadata = dict(
		collection="opensource",
		licenseurl="https://creativecommons.org/publicdomain/mark/1.0/"
		mediatype="texts",
		subject="journals",
		identifier-doi=doi,
		external-identifier=[doi]+m.get('alternative-id')
		originalurl="https://doi.org/{}".format(doi)
		source="https://doi.org/{}".format(doi)
		article-type=m.get('type')
		creator="; ".join([' '.join([a.get('given'), a.get('family')]) for a in m.get('author')]))
		date=m.get('created').get('date-time')[:10]
		description=m.get('abstract') + '<hr>\n<a href="https://unpaywall.org/{}">This paper</a> is in the public domain in USA. Metadata from the CrossRef API, see <a href="https://api.crossref.org/works/{}">full record</a>'.format(doi, doi)
		isbn="; ".join(m.get('ISBN'))
		issn="; ".join(m.get('ISSN'))
		journalabbrv=m.get('short-container-title')
		journaltitle=' '.join(m.get('container-title'))
		language=m.get('language')
		pagerange=m.get('page')
		publisher=m.get('publisher')
		publisher_location=m.get('publisher-location')
		title=m.get('title')[0]
		volume=m.get('issue')
	)

	identifier = re.sub('[^-_A-Za-z0-9]', '_', doi)
	r = upload(identifier, files={identifier+'.pdf': quote_plus(doi)+'.pdf'}, metadata=metadata)
