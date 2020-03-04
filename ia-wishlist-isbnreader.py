#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
   Shell interface to identify books in the Internet Archive wishlist.
   Can be used with a barcode reader which prints ISBN and a newline.
"""
#
# (C) Federico Leva, 2020
#
# Distributed under the terms of the MIT license.
#
__version__ = '0.1.0'

import cmd
from isbnlib import meta
import requests
import sys

class IsbnWishlistShell(cmd.Cmd):
	intro = "Welcome to the ISBN shell for the Internet Archive wishlist. Type help or ? to list commands.\n"
	prompt = "(isbn) "
	verbose = False
	file = None

	def preloop(self):
		"Produce list of wanted ISBNs from the most recent IA wishlist"
		with open("wishlist.txt", "r+") as txt:
			if "978" not in txt.readline():
				ia = requests.get("https://archive.org/download/open_libraries_wish_list/wishlist-latest.tsv")
				txt.write(ia.text)
			txt.seek(0)
			self.isbns = set(txt.read().splitlines())

	def default(self, line):
		"Accept an input line which is just an ISBN, as a barcode reader would print"
		if line.startswith("978"):
			self.do_isbn(line)

	def do_isbn(self, arg):
		"Look for the ISBN in the list"
		if arg in self.isbns:
			print("ISBN wanted: {}\a".format(arg))
			if self.verbose:
				try:
					data = meta(arg, service="openl")
					print("{}\t{}\t{}\t{}".format(data["ISBN-13"], data["Title"], "; ".join(data["Authors"]), data["Year"]))
				except:
					print("INFO: OpenLibrary.org does not known this ISBN")
		else:
			print("ISBN not wanted: {}".format(arg))

	def do_verbose(self, arg):
		"Start verbose mode: fetch metadata over the network and print it"
		self.verbose = True

	def do_exit(self, arg):
		"Stop recording, close the window, and exit:  EXIT"
		print('Thank you for hunting books for the Internet Archive')
		self.close()
		return True

	# ----- record and playback -----
	def do_record(self, arg):
		'Save future commands to filename:  RECORD rose.cmd'
		self.file = open(arg, 'w')
	def do_playback(self, arg):
		'Playback commands from a file:  PLAYBACK rose.cmd'
		self.close()
		with open(arg) as f:
			self.cmdqueue.extend(f.read().splitlines())
	def precmd(self, line):
		line = line.lower()
		if self.file and 'playback' not in line:
			print(line, file=self.file)
		return line
	def close(self):
		if self.file:
			self.file.close()
			self.file = None

if __name__ == '__main__':
	IsbnWishlistShell().cmdloop()
