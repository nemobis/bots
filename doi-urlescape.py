#!/usr/bin/python
# -*- coding: utf-8  -*-
""" Simple script to read a list of DOIs and print it URL escaped. """
#
# (C) Federico Leva, 2018
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'
try:
	from urllib import quote_plus
except:
	from urllib.parse import quote_plus
import sys

dois = open(sys.argv[1], 'r')
if len(sys.argv) > 2:
	out = open(sys.argv[2], 'w')

for doi in dois.readlines():
	doi = doi.strip()
	if len(sys.argv) > 2:
		out.write(quote_plus(doi))
	else:
		print quote_plus(doi)
