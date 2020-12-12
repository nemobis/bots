#!/usr/bin/python3
# -*- coding: utf-8  -*-
""" Bot to download archiviolastampa.it """
#
# (C) Federico Leva, 2020
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.2.0'

import csv
import datetime
from internetarchive import get_item, upload
import json
import os
from pathlib import Path
import re
import requests
import sys
from time import sleep
import zipfile

def getDayId(day, headboard='01'):
	"""
	Get the magic ID of the day from the index of the next day.
	Takes day in datetime format and issue type (01 or 02) as string.
	"""

	next_day = (day + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
	url = "http://www.archiviolastampa.it/index2.php?option=com_lastampa&task=issue&no_html=1&type=neighbors&headboard={}&date={}%2000:00:00".format(headboard, next_day)
	index = requests.get(url)

	# Expected output is something like:
	# {"previousIssueId":"1319_02_1989_0242_0001","nextIssueId":"1319_02_1989_0244_0001"} 
	if index.status_code < 300:
		return index.json()['previousIssueId']

def getIssueMetadata(identifier):
	""" Issue metadata from the identifier """

	url = "http://www.archiviolastampa.it/index2.php?option=com_lastampa&task=issue&no_html=1&type=info&issueid={}".format(identifier)
	info = requests.get(url)

	# Expected output is something like:
	# {"id_testata":"02","uscita":"243","data_uscita":"1989-09-13 00:00:00","nome_testata":"Europa"} 
	if info.status_code < 300 and "data_uscita" in info.text:
		return info.json()

def readIssueMetadata(day):
	""" Read issue metadata from the JSON saved in the day's directory, return title and issue """

	nome_testata = "La Stampa"
	uscita = None
	with open(day + '/issue_metadata.json', 'r') as j:
		try:
			metadata = json.load(j)
			title = metadata.get('nome_testata', 'La Stampa')
			issue = metadata.get('uscita', None)
			id_testata = metadata.get('id_testata', '01')
		except json.decoder.JSONDecodeError:
			print("WARNING: Could not open JSON for day {}".format(day))
			return
		return title, issue, id_testata

def makeDay(day, metadata):
	""" Prepare the download of this day, if appropriate """

	day_ymd = day.strftime('%Y-%m-%d')
	if day_ymd in metadata['data_uscita']:
		try:
			os.mkdir(day_ymd)
		except FileExistsError:
			print("INFO: Day {} was already done".format(day_ymd))
			return False

		# FIXME: Should use cross-platform path joining here and below.
		with open('{}/issue_metadata.json'.format(day_ymd), 'w') as jsonout:
			jsonout.write(json.dumps(metadata))
		return True
	else:
		# We got a different day, probably there's a gap for festivities.
		return False

def downloadDay(day, headboard='01'):
	""" Retrieve data for issue, prepare files and download images """

	day_ymd = day.strftime('%Y-%m-%d')
	incomplete = None
	identifier = getDayId(day, headboard)
	# TODO: Add a timestamp so it's easier to spot stuck downloaders.
	print("INFO: Found {} for {}".format(identifier, day.strftime('%Y-%m-%d')))
	metadata = getIssueMetadata(identifier)
	sleep(0.1)
	if not metadata:
		# Sometimes the response is simply an empty page, for instance:
		# INFO: Found 1066_01_1980_0230_0002 for 1980-10-20
		# Expecting value: line 1 column 1 (char 0)
		print("WARNING: could not download metadata for {}".format(day_ymd))
		# Just keep going. TODO: Some logging?
		metadata = {'data_uscita': day_ymd}

	if not makeDay(day, metadata):
		# We got a different day, probably there's a gap for festivities.
		return None

	# Prepare a session for this issue
	# TODO: Add a timeout here or to requests.
	s = requests.Session()
	# We need the parameter from the hidden input
	# <input type="hidden" name="t" value="a2016dedff5843c652d2fdf4f87055cc" />
	home = s.get('http://www.archiviolastampa.it/')
	t = re.findall('<input type="hidden" name="t" value="([a-z0-9]+)"', home.text)[0]
	sleep(0.1)

	# List pages in the issue
	pages = s.get('http://www.archiviolastampa.it/load.php?url=/item/getPagesInfo.do?id={}&s={}'.format(identifier, t))
	with open('{}/{}_pages.json'.format(day_ymd, identifier), 'w') as pages_out:
		pages_out.write(pages.text)
	sleep(0.1)

	for page in pages.json()['pageList']:
		page_id = page['thumbnailId']
		page_image = s.get('http://www.archiviolastampa.it/load.php?url=/downloadContent.do?id={}_19344595&s={}'.format(page_id, t))
		# TODO: might want to handle connection errors
		# HTTPConnectionPool(host='www.archiviolastampa.it', port=80): Max retries exceeded with url: ... (Caused by NewConnectionError('<requests.packages.urllib3.connection.HTTPConnection object at 0x7f8a235d1c88>: Failed to establish a new connection: [Errno 110] Connection timed out',))
		sleep(1.0)
		if not 'image/jpeg' in page_image.headers['Content-Type']:
			print("WARNING: could not download an image for {}".format(page_id))
			incomplete = True
			sleep(30)
			continue
		with open('{}/{}.jpg'.format(day_ymd, page_id), 'wb') as page_out:
			page_out.write(page_image.content)

		page_data = s.get('http://www.archiviolastampa.it/load.php?url=/search/select/?wt=json&q=pageID:{}&s={}&s={}'.format(page_id, t, t))
		with open('{}/{}_pagedata.json'.format(day_ymd, page_id), 'w') as page_meta:
			page_meta.write(page_data.text)
		sleep(0.1)

	if incomplete:
		return False
	return True

def listDates(start='1867-02-09', end='2005-12-31'):
	""" Return list of days between two dates """

	first_day = datetime.datetime.strptime(start, '%Y-%m-%d')
	last_day = datetime.datetime.strptime(end, '%Y-%m-%d')
	return [first_day + datetime.timedelta(days=x) for x in range(0, (last_day-first_day).days+1)]

def getDayCounts(day):
	""" Return imagecount, pagecount and identifier from the files in a day directory """

	imagecount = 0
	pagecount = 0
	identifier = ''
	for dayfile in Path(day).iterdir():
		if dayfile.name.endswith('_images.zip'):
			arc = zipfile.ZipFile(day + '/' + dayfile.name)
			imagecount = len([image.filename for image in arc.infolist() if image.filename.endswith('jpg')])
		if dayfile.name.endswith('_pages.json'):
			identifier = dayfile.name.replace('_pages.json', '')
			with open(day + '/' + dayfile.name, 'r') as j:
				try:
					pages = json.load(j)
					pagecount = len(pages['pageList'])
				except json.decoder.JSONDecodeError:
					print("WARNING: Could not open JSON for day {}".format(day))
					pass
	return imagecount, pagecount, identifier

def verifyDirectory():
	""" Verify the contents of the archives of the current directory """

	complete = True
	csvout = open('issue-counts.csv', 'w')
	writer = csv.writer(csvout,
			delimiter='\t',
			lineterminator='\n',
			quoting=csv.QUOTE_MINIMAL,
			)
	writer.writerow(['Date', 'Image count', 'Page count', 'Identifier'])

	days = set([d.name for d in Path('.').iterdir() if re.match('[0-9-]{10}', d.name)])
	for day in days:
		imagecount, pagecount, identifier = getDayCounts(day)
		if imagecount > 0 and pagecount > 0 and imagecount != pagecount:
			print("ERROR: Day {} has {} images for {} expected pages".format(day, imagecount, pagecount))
			complete = False
		writer.writerow([day, imagecount, pagecount, identifier])

	return complete

def getBasicItemData():
	""" Return a dictionary with the metadata which is the same for all Internet Archive items """

	metadata = {
		"collection": "opensource",
		"licenseurl": "https://creativecommons.org/licenses/by-nc-nd/2.5/it/",
		"mediatype": "texts",
		"subject": "newspapers; giornali; La Stampa; Archivio Storico La Stampa",
		"creator": "Editrice La Stampa",
		"contributor": "CSI Piemonte",
		"fixed-ppi": 300,
		"sponsor": "Comitato per la Biblioteca dell'Informazione Giornalistica; CBDIG; Regione Piemonte; Compagnia di San Paolo; Fondazione CRT; Editrice La Stampa",
		"journaltitle": "La Stampa",
		"title": "La Stampa",
		"language": "Italian",
		"publisher": "Editrice La Stampa S.p.A.",
		"publisher_location": "Torino, Italia",
		"originalurl": "http://www.archiviolastampa.it/", # TODO: "source" does not seem to do much good
		"notes": "Per i titoli, le parole chiave e il testo contenuti fare riferimento all'OCR originale di ciascuna pagina all'interno dell'archivio allegato con suffisso _pagedata.zip (pulsante \"ZIP\" sotto \"Download options\"), altrimenti si faccia uso del nuovo OCR indicizzato dal motore di ricerca di Internet Archive e mostrato negli altri documenti allegati.",
		"rights": """This work or parts of this work may be in the public domain. The publisher, Editrice La Stampa, while distributing the scans under cc-by-nc-nd-2.5-it license, made the following claims. ∎ Le singole pagine di ciascun numero (ma non il numero considerato nella sua interezza) dei quotidiani "La Stampa" e "Stampa Sera" e delle altre pubblicazioni dell'Editrice La Stampa S.p.A. presenti all'interno dell'Archivio Storico sono rilasciate in licenza Creative Commons Attribuzione - Non commerciale - Non opere derivate 2.5.
https://creativecommons.org/licenses/by-nc-nd/2.5/legalcode.it
Nella successiva riproduzione e distribuzione delle pagine dei quotidiani "La Stampa" e "Stampa Sera" e delle altre pubblicazioni dell'Editrice La Stampa S.p.A. presenti all'interno dell'Archivio Storico, l'utente è tenuto ad indicare - come autore dell'Opera - l'Editrice La Stampa S.p.A. e menzionare la fonte da cui tale Opera è stata tratta.
I numeri del quotidiano "La Stampa" e "Stampa Sera" e delle altre pubblicazioni dell'Editrice La Stampa S.p.A. pubblicati per la prima volta da oltre 70 anni sono ovviamente di pubblico dominio e liberamente utilizzabili, in tutto o in parte, dagli utenti al di fuori dei termini della licenza Creative Commons, fermo restando l'obbligo di indicare l'autore dell'opera.
La licenza Creative Commons non ha ad oggetto i singoli articoli, individualmente considerati, pubblicati sul quotidiano "La Stampa" e "Stampa Sera" e sulle altre pubblicazioni dell'Editrice La Stampa S.p.A. presenti all'interno dell'Archivio Storico, la cui riproduzione è pertanto vietata. Gli articoli di autori deceduti da oltre 70 anni sono tuttavia di pubblico dominio e liberamente utilizzabili dagli utenti, fermo restando l'obbligo di indicare l'autore dell'articolo. Restano, inoltre, impregiudicati i diritti di utilizzo dei singoli articoli riconosciuti dalla legge sul diritto d'autore (Legge 22 aprile 1941 n. 633 e successive modifiche), nei casi ed entri i limiti previsti dalla legge medesima.
La licenza Creative Commons non ha ad oggetto la banca dati dell'Archivio Storico: è conseguentemente vietata l'estrazione e il reimpiego della totalità o di una parte sostanziale del contenuto di tale banca dati. Restano impregiudicati i diritti sulla banca dati riconosciuti dalla legge sul diritto d'autore (Legge 22 aprile 1941 n. 633 e successive modifiche), nei casi ed entri i limiti previsti dalla legge medesima.
La licenza Creative Commons non ha ad oggetto le singole foto ed i singoli articoli, individualmente considerati, pubblicati sul quotidiano "La Stampa" e "Stampa Sera" e sulle altre pubblicazioni dell'Editrice La Stampa S.p.A. presenti all'interno dell'Archivio Storico, la cui riproduzione è pertanto vietata.""",
	}

	return metadata

def uploadDay(day):
	""" Upload the archives in the directory for this day to the Internet Archive """

	imagecount, pagecount, stampaid = getDayCounts(day)
	md = getBasicItemData()
	md["title"], md["issue"], id_testata = readIssueMetadata(day)
	md["title"] = md["title"] + " ({})".format(day)
	md["external-identifier"] = "urn:archiviolastampa:{}".format(stampaid)
	# md["originalurl"] = "http://www.archiviolastampa.it/index2.php?option=com_lastampa&task=issue&no_html=1&type=info&issueid={}".format(stampaid)
	md["date"] = day
	md["pages"] = pagecount
	md["description"] = "Numero intero del giorno {} dall'archivio storico La Stampa.".format(day)

	# TODO: Needle defaults to 01. Maybe read the prefix in the actual files instead?
	if id_testata == "02":
		identifier = "stampa-sera_{}".format(day)
	else:
		identifier = "lastampa_{}".format(day)

	try:
		item = get_item(identifier)
		if item and item.item_size:
			print("INFO: Day {} was already uploaded at {}, size {}. Skipping.".format(day, identifier, item.item_size))
			return True

		iafiles = [day + '/' + arc.name for arc in Path(day).iterdir()]
		print("INFO: Uploading day {} with {} files".format(day, len(iafiles)))
		r = upload(identifier, files=iafiles, metadata=md, retries=5, retries_sleep=300)
		if r[0].status_code < 400:
			return True
	except Exception as e:
		print("ERROR: Upload failed for day {}".format(day))
		print(e)
		return False

def main(argv=None):
	# TODO: Hacky commandline arguments are hacky!
	if argv[1] == "verify":
		return verifyDirectory()

	if argv[1] == "upload":
		days = set([d.name for d in Path('.').iterdir() if re.match('[0-9-]{10}', d.name)])
		for day in sorted(list(days)):
			uploadDay(day)
			sleep(5)
		return

	retry = open('retry.log', 'a')
	for day in listDates(argv[2], argv[3]):
		day_ymd = day.strftime('%Y-%m-%d')
		if os.path.isdir(day_ymd):
			print("INFO: Day {} was already done".format(day_ymd))
			continue
		try:
			download = downloadDay(day, headboard=argv[1])
			# TODO: Also take care of compression and verification
			sleep(2)
		except Exception as e:
			print(e)
			download = False
		if download is None:
			print("INFO: Nothing to do for {}".format(day))
			continue
		if download is False:
			print("ERROR: Something went wrong with {}, please retry. Sleeping now.".format(day))
			retry.write("{}\n".format(day))
			sleep(30)
			
	retry.close()
if __name__ == "__main__":
	main(sys.argv)
