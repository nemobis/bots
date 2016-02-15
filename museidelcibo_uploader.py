#!/usr/bin/python
# -*- coding: utf-8  -*-
""" Bot to read a Musei del cibo CSV file and upload files to Commons. """
#
# (C) Federico Leva, 2016
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'

import pywikibot
import pywikibot.data.api
from pywikibot import config
from upload import UploadRobot
#import sys
import os
#import re
from collections import namedtuple
import unicodecsv as csv
from kitchen.text.converters import to_unicode

class CiboRobot:

    def __init__(self, filename):
        self.repo = pywikibot.Site('commons', 'commons')
        self.filename = filename
        if not os.path.exists(self.filename):
            pywikibot.output('Cannot find %s. Try providing the absolute path.'
                             % self.filename)
            sys.exit(1)

    def run(self, filename):
        with open(filename, 'r') as f:
            source = csv.reader(f, delimiter='\t')
            header = next(source)
            pywikibot.output("Header of the input table: " + ', '.join(header) )
            titles = namedtuple('titles', ', '.join(header))
            titles = [titles._make(row) for row in source]

        if not titles:
            pywikibot.output("We were not able to extract the data to work on. Exiting.")
            return

        for row in titles:
            commons = "%s - Musei del cibo - %s - %s.tif" % (row.nome, row.museo, row.inventario)
            description = u"""
{{Musei del cibo
| museo = %s
| inventario = %s
| nome = %s
| ambito = %s
| epoca = %s
| dimensioni = %s
| materia = %s
| descrizione = %s
| provenienza = %s
| note = %s
}}
""" % (row.museo, row.inventario, row.nome, row.ambito, row.epoca,
    row.dimensioni, row.materia, row.descrizione, row.provenienza, row.note)

            try:
                upload = UploadRobot(row.inventario + ".tif", description=description,
                                     useFilename=commons, keepFilename=True,
                                     verifyDescription=False, ignoreWarning=True, aborts=True)
                upload.run()
            except:
                pywikibot.output("ERROR: The upload could not be completed.")

def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """

    # process all global bot args
    # returns a list of non-global args
    for arg in pywikibot.handle_args(args):
        if arg:
            if arg.startswith('-file'):
                filename = arg[6:]

    bot = CiboRobot(filename)
    bot.run(filename)

if __name__ == "__main__":
    main()