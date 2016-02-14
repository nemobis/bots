#!/usr/bin/python
# -*- coding: utf-8  -*-
""" Bot to scrape a list of EasyChair submissions and upload them to a wiki """
#
# (C) Federico Leva, 2016
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'

import requests
from lxml import html
import re
from kitchen.text.converters import to_bytes

cj = requests.utils.cookiejar_from_dict( { "cool2": "blabla", "cool1": "blabla2" } )
headers = {"User-Agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0" }
index = requests.get("https://easychair.org/conferences/submission_show_all.cgi?a=123456789", cookies=cj, headers=headers)
indexdata = html.fromstring(index.text)
urls = indexdata.xpath('//a[contains(@href,"submission_info_show.cgi")]/@href')
export = open("easychair-submissions.txt", "w+")

for url in urls:
	sub = html.fromstring(requests.get("https://easychair.org/conferences/" + url, cookies=cj, headers=headers).text)
	title = sub.xpath('//td[text()="Title:"]/../td[2]/text()')[0].strip()
	names = sub.xpath('//b[text()="Authors"]/../../..//tr[@id!="row37"]/td[1]/text()')
	surnames = sub.xpath('//b[text()="Authors"]/../../..//tr[@id!="row37"]/td[2]/text()')
	countries = sub.xpath('//b[text()="Authors"]/../../..//tr[@id!="row37"]/td[4]/text()')
	topic = sub.xpath('//span[text()="Topics:"]/../../td[2]/text()')[0].strip()
	abstract = sub.xpath('//td[text()="Abstract:"]/../td[2]/text()')[0].strip()
	result = sub.xpath('//td[text()="Decision:"]/../td[2]/text()')[0].strip()
	keywords = sub.xpath('//div[parent::td[@class="value"]]/text()')
	number = re.findall("[0-9]+", sub.xpath('//div[@class="pagetitle"]/text()')[0])[0]

	categories = u""
	authors = u""
	for keyword in keywords:
		categories = categories + u"*%s [[Category:%s]]\n" % (keyword, keyword)
	for i in range(0, len(names)):
		authors = authors + "* %s %s\n" % (names[i], surnames[i])
	pagetitle = u"Critical issues presentations/%s" % title

	template = u"""
START
'''%s'''
{{Submission
|no= %s
|title= %s
|author=
%s
|country= %s
|topic= %s
|keywords=
%s
|abstract= %s
|result= %s
}}
END
""" % (pagetitle, number, title, authors, ";".join(countries), topic, categories, abstract, result)

	export.write(to_bytes(template))
