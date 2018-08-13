#!/usr/bin/python
# -*- coding: utf-8  -*-
""" Bot to download a list of PDFs from given URLs in Selenium. """
#
# (C) Federico Leva, 2018
#
# Distributed under the terms of the MIT license.
#

from xvfbwrapper import Xvfb
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import selenium.common.exceptions
from time import sleep
import random

vdisplay = Xvfb()

def getDriver():
    # https://stackoverflow.com/a/47075896
    # http://stackoverflow.com/questions/12698843/ddg#12698844
    chrome_options = Options()
    prefs = { #"download.default_directory": "~",
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            #"plugins.plugins_disabled": ["Chrome PDF Viewer"]
            }
    chrome_options.add_experimental_option("prefs", prefs)
    return webdriver.Chrome(chrome_options=chrome_options)

def downloadUrl(driver, url=None):
    actions = webdriver.ActionChains(driver)
    driver.get(url)
    sleep(1)
    try:
        elem = driver.find_element_by_css_selector(".stats-document-lh-action-downloadPdf_2")
    except selenium.common.exceptions.NoSuchElementException:
        print "Could not click on %s" % url
        return
    actions.click(elem)
    actions.perform()
    sleep(random.randint(10, 40))

def main(argv=None):
    #with Xvfb() as xvfb:
    with open('urls.txt', 'rb') as urls:
        driver = getDriver()
        for url in urls.readlines():
            downloadUrl(driver, url.strip())

if __name__ == "__main__":
    main()
