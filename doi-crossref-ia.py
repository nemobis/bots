#!/usr/bin/python
# -*- coding: utf-8  -*-
""" Bot to upload PDFs for a list of DOIs to the Internet Archive. """
#
# (C) Federico Leva, 2018
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'
from internetarchive import upload
try:
	from urllib import quote_plus
except:
	from urllib.parse import quote_plus
import re
import requests
s = requests.Session()

def upload_doi(doi=None):
	m = s.get('https://api.crossref.org/works/{}?mailto=openaccess@wikimedia.it'.format(doi)).json()['message']

	md = {
		"collection": "opensource",
		"licenseurl": "https://creativecommons.org/publicdomain/mark/1.0/",
		"mediatype": "texts",
		"subject": "journals",
		"identifier-doi": doi,
		"external-identifier": [doi]+(m.get('alternative-id') or []),
		"originalurl": "https://doi.org/{}".format(doi),
		"source": "https://api.crossref.org/works/{}".format(doi),
		"article-type": m.get('type'),
		"creator": "; ".join([' '.join([a.get('given', ''), a.get('family', '')]) for a in m.get('author', [])]),
		"date": "-".join([str(d).zfill(2) for d in m.get('published-print', []).get('date-parts', [])[0]]),
		"description": m.get('abstract', '') + '<hr>\nThis paper is in the public domain in USA. Metadata comes from the CrossRef API, see full record in the source URL below.'.format(doi, doi),
		"isbn": "; ".join(m.get('ISBN', [])),
		"issn": "; ".join(m.get('ISSN', [])),
		"journalabbrv": m.get('short-container-title'),
		"journaltitle": ' '.join(m.get('container-title', [])),
		"language": m.get('language'),
		"pagerange": m.get('page'),
		"publisher": m.get('publisher'),
		"publisher_location": m.get('publisher-location'),
		"title": m.get('title')[0],
		"volume": m.get('issue')
	}

	identifier = 'paper-doi-' + re.sub('[^-_A-Za-z0-9]', '_', doi)[:89]
	r = upload(identifier, files={identifier+'.pdf': quote_plus(doi)+'.pdf'}, metadata=md)

if __name__ == '__main__':
	dois = open('dois.txt', 'r')
	for doi in dois.readlines():
		doi = doi.strip()
		print("Looking up DOI: {}".format(doi))
		upload_doi(doi)
