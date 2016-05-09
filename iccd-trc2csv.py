#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Script to convert an ICCD TRC file to CSV format.
The input file is assumed to be UTF-8 with UNIX line ending.
"""
#
# (C) Federico Leva, 2016
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'

import codecs
import unicodecsv as csv
from collections import namedtuple
import os
import re
import sys

# Campi ripetibili
# http://www.iccd.beniculturali.it/index.php?it/473/standard-catalografici/Standard/29
rip = ['AAT', 'ACC', 'ACS', 'ADM', 'ADT', 'AGG', 'AGGF', 'AGGR', 'AIN', 'ALN', 'ATB', 'ATBM', 'AUT', 'AUTM', 'BIB', 'BIL', 'CDGI', 'CDGS', 'CMM', 'CMMN', 'CMPN', 'DESI', 'DESS', 'DRA', 'DSCA', 'DSCF', 'DTM', 'EDT', 'ESP', 'FNT', 'FTA', 'FUR', 'INV', 'ISP', 'ISR', 'MIS', 'MISV', 'MST', 'MSTD', 'MSTL', 'MTC', 'NVC', 'NVCD', 'RCGA', 'RCGS', 'REG', 'REI', 'ROZ', 'RSE', 'RSR', 'RST', 'RSTN', 'RSTR', 'RVES', 'SGTI', 'SGTT', 'STI', 'STM', 'VDC']

trc = codecs.open('iccd.trc', 'r', encoding='utf-8')
records = trc.read().split('CD:\n')[1:]
trc.close()
data = []

for i in range(0, len(records)-1):
	data.append({})
	counter = {}
	record = re.sub(r'\n {6}', '', records[i])
	for field in record.splitlines():
		datum = field.split(': ', 1)
		if len(datum) < 2:
			# This must be a 2 or 3 letters code without content
			datum = field.split(':', 1)
			# Take note of which iteration of this field we're at, to properly store subfields.
			if datum[0] in rip:
				if datum[0] in counter:
					counter[datum[0]] += 1
				else:
					counter[datum[0]] = 1
			continue
		if datum[0] not in rip:
			if datum[0][:-1] not in rip:
				# We're in luck! Just add the field to our table.
				data[i][datum[0]] = datum[1]
			else:
				data[i][datum[0][:-1] + str(counter[datum[0][:-1]]) + datum[0][-1]] = datum[1]
		else:
			if datum[0][:-1] not in rip:
				data[i][datum[0] + '1'] = datum[1]
			else:
				data[i][datum[0][:-1] + str(counter[datum[0][:-1]]) + datum[0][-1] + '1'] = datum[1]

# Prepare to write out to CSV
fieldnames = {}
header = []
for i in range(0, len(data)-1):
	for key in data[i].iterkeys():
		fieldnames[key] = True
for name in fieldnames.iterkeys():
	header.append(name)
print(header)
table = namedtuple('table', ', '.join(header))
table = [table._make(row) for row in data]
with codecs.open('iccd.csv', 'w', encoding='utf-8') as csvfile:
	out = csv.writer(csvfile, delimiter='\t',
				  lineterminator='\n',
				  quoting=csv.QUOTE_MINIMAL)
	out.writerow(header)
	for row in table:
		out.writerow(row)