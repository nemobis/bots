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
from collections import namedtuple, defaultdict
import os
import re
import sys
import subprocess
# Uploader
import pywikibot
import pywikibot.data.api
from pywikibot import config
from upload import UploadRobot

# Campi ripetibili
# http://www.iccd.beniculturali.it/index.php?it/473/standard-catalografici/Standard/29
rip = ['AAT', 'ACC', 'ACS', 'ADM', 'ADT', 'AGG', 'AGGF', 'AGGR', 'AIN', 'ALN', 'ATB', 'ATBM', 'AUT', 'AUTM', 'BIB', 'BIL', 'CDGI', 'CDGS', 'CMM', 'CMMN', 'CMPN', 'DESI', 'DESS', 'DRA', 'DSCA', 'DSCF', 'DTM', 'EDT', 'ESP', 'FNT', 'FTA', 'FUR', 'INV', 'ISP', 'ISR', 'MIS', 'MISV', 'MST', 'MSTD', 'MSTL', 'MTC', 'NVC', 'NVCD', 'RCGA', 'RCGS', 'REG', 'REI', 'ROZ', 'RSE', 'RSR', 'RST', 'RSTN', 'RSTR', 'RVES', 'SGTI', 'SGTT', 'STI', 'STM', 'VDC']

trc = codecs.open('iccd.trc', 'r', encoding='utf-8')
records = trc.read().split('CD:\n')[1:]
trc.close()
data = []

for i in range(0, len(records)-1):
	data.append({})
	counter = defaultdict(int)
	record = re.sub(r'\n {6}', '', re.sub(r'\.\n {6}', ' ', records[i]))
	for field in record.splitlines():
		datum = field.split(': ', 1)
		if len(datum) < 2:
			# This must be a 2 or 3 letters code without content
			datum = field.split(':', 1)
			# Take note of which iteration of this field we're at, to properly store subfields.
			if datum[0] in rip:
				counter[datum[0]] += 1
			continue
		else:
			# Take note of which iteration of this field we're at, to properly store subfields.
			if datum[0] in rip:
				counter[datum[0]] += 1
		if datum[0] not in rip:
			if datum[0][:-1] not in rip:
				# We're in luck! Just add the field to our table.
				data[i][datum[0]] = datum[1]
			else:
				data[i][datum[0][:-1] + str(counter[datum[0][:-1]]) + datum[0][-1]] = datum[1]
		else:
			if datum[0][:-1] not in rip:
				data[i][datum[0] + str(counter[datum[0]])] = datum[1]
			else:
				data[i][datum[0][:-1] + str(counter[datum[0][:-1]]) + datum[0][-1] + str(counter[datum[0]])] = datum[1]

# Anticipate the upload here until we get the CSV writing fixed
# FIXME: split and actually save to csvfile

for i in range(0, len(data)-1):
	description = u"""{{ICCD TRC
| institution = {{institution:Museoscienza}}
| permission =  {{cc-by-sa-4.0}}
"""
	filenames = []
	directory = './Foto_CATALOGO_01/%s_foto/' % data[i]['IDK'].split('-')[0].strip()
	for key in data[i].iterkeys():
		if key == "IDK":
			description += "| source = {{Museoscienza|idk=%s}}\n" % data[i]['IDK']
		else:
			description += u"| %s = %s\n" % (key, data[i][key])
		if re.match('FTA[0-9]+I', key):
			filenames.append(directory + data[i][key])
	description += u"}}"

	# The filenames may have excess leading zeros, but we do not want partial matches.
	needle = r'(^|[^0-9])0*%s[^0-9]' % re.sub('[^0-9]', '', data[i]['INV1N'])
	for image in os.listdir(directory):
		if re.match(needle, image):
			filenames.append(directory + image)
	if not filenames:
		print "ERROR: No files found for record %s, inventory %s" % (data[i]['IDK'], data[i]['INV1N'])
		continue

	for filename in filenames:
		try:
			prefix = "%s %s" % (data[i]['OGTD'], data[i]['OGTT'])
		except:
			prefix = data[i]['OGTD']
		prefix = re.sub('[#<>\[\]|{}/?]', '', prefix)
		commons = u"%s - Museo scienza tecnologia Milano %s" % (prefix, filename.split('/')[-1])
		print commons
		try:
			upload = UploadRobot(filename, description=description,
								useFilename=commons, keepFilename=True,
								verifyDescription=False, ignoreWarning=False, aborts=True)
			upload.run()
			os.remove(filename)
		except:
			pywikibot.output("ERROR: The upload could not be completed.")

"""
# Prepare to write out to CSV: find out what columns we need
fieldnames = {}
header = []
for i in range(0, len(data)-1):
	for key in data[i].iterkeys():
		fieldnames[key] = True
for name in fieldnames.iterkeys():
	header.append(name)
print(header)

# Fill the blanks and get an actual table
for i in range(0, len(data)-1):
	for column in header:
		if column not in data[i]:
			data[i][column] = u""
table = namedtuple('table', ', '.join(header))
table = [table._make(row) for row in data]

# Actually write out to CSV
with codecs.open('iccd.csv', 'w', encoding='utf-8') as csvfile:
	out = csv.writer(csvfile, delimiter='\t',
				lineterminator='\n',
				quoting=csv.QUOTE_MINIMAL)
	out.writerow(header)
	for row in table:
		out.writerow(row)
"""
