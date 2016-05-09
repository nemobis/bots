#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Script to list all Google Books URLs and IDs by scraping the Internet Archive's
Wayback machine CDX index.
https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md
"""
#
# (C) Federico Leva and ArchiveTeam, 2016
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'

import requests
import bz2
import os

# List from https://www.iana.org/domains/root/db
tld = ['com', 'ac', 'ad', 'ae', 'af', 'ag', 'ai', 'al', 'am', 'an', 'ao', 'aq', 'ar', 'as', 'at', 'au', 'aw', 'ax', 'az', 'ba', 'bb', 'bd', 'be', 'bf', 'bg', 'bh', 'bi', 'bj', 'bl', 'bm', 'bn', 'bo', 'bq', 'br', 'bs', 'bt', 'bv', 'bw', 'by', 'bz', 'ca', 'cc', 'cd', 'cf', 'cg', 'ch', 'ci', 'ck', 'cl', 'cm', 'cn', 'co', 'cr', 'cu', 'cv', 'cw', 'cx', 'cy', 'cz', 'de', 'dj', 'dk', 'dm', 'do', 'dz', 'ec', 'ee', 'eg', 'eh', 'er', 'es', 'et', 'eu', 'fi', 'fj', 'fk', 'fm', 'fo', 'fr', 'ga', 'gb', 'gd', 'ge', 'gf', 'gg', 'gh', 'gi', 'gl', 'gm', 'gn', 'gp', 'gq', 'gr', 'gs', 'gt', 'gu', 'gw', 'gy', 'hk', 'hm', 'hn', 'hr', 'ht', 'hu', 'id', 'ie', 'il', 'im', 'in', 'io', 'iq', 'ir', 'is', 'it', 'je', 'jm', 'jo', 'jp', 'ke', 'kg', 'kh', 'ki', 'km', 'kn', 'kp', 'kr', 'kw', 'ky', 'kz', 'la', 'lb', 'lc', 'li', 'lk', 'lr', 'ls', 'lt', 'lu', 'lv', 'ly', 'ma', 'mc', 'md', 'me', 'mf', 'mg', 'mh', 'mk', 'ml', 'mm', 'mn', 'mo', 'mp', 'mq', 'mr', 'ms', 'mt', 'mu', 'mv', 'mw', 'mx', 'my', 'mz', 'na', 'nc', 'ne', 'nf', 'ng', 'ni', 'nl', 'no', 'np', 'nr', 'nu', 'nz', 'om', 'pa', 'pe', 'pf', 'pg', 'ph', 'pk', 'pl', 'pm', 'pn', 'pr', 'ps', 'pt', 'pw', 'py', 'qa', 're', 'ro', 'rs', 'ru', 'rw', 'sa', 'sb', 'sc', 'sd', 'se', 'sg', 'sh', 'si', 'sj', 'sk', 'sl', 'sm', 'sn', 'so', 'sr', 'ss', 'st', 'su', 'sv', 'sx', 'sy', 'sz', 'tc', 'td', 'tf', 'tg', 'th', 'tj', 'tk', 'tl', 'tm', 'tn', 'to', 'tp', 'tr', 'tt', 'tv', 'tw', 'tz', 'ua', 'ug', 'co.uk', 'um', 'us', 'uy', 'uz', 'va', 'vc', 've', 'vg', 'vi', 'vn', 'vu', 'wf', 'ws‎', 'ye', 'yt', 'za', 'zm', 'zw']
with bz2.BZ2File('ia-googlebooks.cdx.bz2', 'w') as cdx:
	for domain in tld:
		pages = requests.get('https://web.archive.org/cdx/search/cdx?url=books.google.%s/*&showNumPages=true' % domain)
		n = int(pages.text)
		if n < 1:
			continue
		for i in range(0,n-1):
			gb = requests.get('https://web.archive.org/cdx/search/cdx?url=books.google.%s/*&page=%d' % (domain, i))
			cdx.write(gb.text)
		print("Downloaded %d CDX pages on books.google.%s" % (n, domain))

# Exclude the lowercased URL and other stuff; "id=" is present and not escaped.
# https://archive.org/web/researcher/cdx_legend.php
os.system('bzcat ia-googlebooks.cdx.bz2 | cut -d " " -f 2,3,4 | grep -Eo "id=\w{12}\W" | grep -Eo "\w{12}" | sort -u >> ia-googlebooks-ids.txt')
os.system('wc -l ia-googlebooks-ids.txt')