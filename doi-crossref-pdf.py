#!/usr/bin/python
# -*- coding: utf-8  -*-
""" Bot to download a list of DOIs from the URLs of the TDM API. """
#
# (C) Federico Leva, 2018
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import requests.exceptions
try:
	from urllib import quote_plus
except:
	from urllib.parse import quote_plus
from time import sleep

dois = open('dois.txt', 'rb')
s = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 502, 503, 504 ])
s.mount('http://', HTTPAdapter(max_retries=retries))
s.mount('https://', HTTPAdapter(max_retries=retries))
headers = { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0' }

for doi in dois.readlines():
	doi = doi.strip()
	print("Looking up DOI: {}".format(doi))
	sleep(1)
	url = None
	try:
		api = s.get('https://api.crossref.org/works/{}'.format(doi)).json()
	except ValueError:
		continue
	if not 'link' in api['message']:
		continue
	for link in api['message']['link']:
		content = link['content-type']
		if content == 'application/pdf':
			url = link['URL']
		if content == 'unspecified' and not url:
			url = link['URL']
	if url:
		try:
			pdf = s.get(url, headers=headers, timeout=10)
		except requests.exceptions.ConnectionError:
			print("ERROR: ConnectionError. Sleeping 10 seconds.")
			sleep(10)
			continue
		if pdf.status_code == 200 and 'pdf' in pdf.headers['Content-Type']:
			print("Saving PDF from {}".format(url))
			with open('{}.pdf'.format(quote_plus(doi)), 'wb') as out:
				out.write(pdf.content)
				continue

# exiftool -overwrite_original -all=
# find . -maxdepth 0 -name "*pdf" -print0 | xargs -P8 -0 -I§ -n1 qpdf --linearize "§" "cleanpdf/§"
