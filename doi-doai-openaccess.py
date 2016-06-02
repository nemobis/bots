#!/usr/bin/env python2
"""
Queries the Wikimedia projects database replica on labsdb to list all
links to DOI documents which are Open Access on DOAI.
Requires Wikimedia Labs labsdb local access.

Usage:
    doi-doai-openaccess.py --help
    doi-doai-openaccess.py <dbname>

Options:
    --help           Prints this documentation
    <dbname>         The dbname of the wiki to search DOIs in [default: enwiki].

Copyright waived (CC-0), Federico Leva, 2016
"""
import docopt
import MySQLdb
import re
import requests

session = requests.Session()

def main(argv=None):

    args = docopt.docopt(__doc__, argv=argv)
    wiki = args['<dbname>']

    for doi in get_doi_el(wiki) | get_doi_iwl(wiki):
        if get_doai_oa(doi):
            print doi

def get_doi_el(wiki):
    """ Set of DOI codes from external links. """

    dois = set([])

    doiquery = """SELECT el_to
    FROM externallinks
    WHERE el_index LIKE 'https://org.doi.dx./10%'
    OR el_index LIKE 'http://org.doi.dx./10%'"""

    connection = MySQLdb.connect(host=wiki + '.labsdb',
                                 db=wiki + '_p',
                                 read_default_file='~/.my.cnf')
    cursor = connection.cursor()
    cursor.execute(doiquery)
    for link in cursor.fetchall():
        doi = re.findall('10.+$', link[0])[0]
        if doi:
            dois.add(doi)
    
    return dois

def get_doi_iwl(wiki):
    """ Set of DOI codes from interwiki links. """

    dois = set([])

    doiquery = """SELECT iwl_title
    FROM iwlinks
    WHERE iwl_prefix = 'doi'
    AND iwl_title LIKE '10%'"""

    connection = MySQLdb.connect(host=wiki + '.labsdb',
                                 db=wiki + '_p',
                                 read_default_file='~/.my.cnf')
    cursor = connection.cursor()
    cursor.execute(doiquery)
    for link in cursor.fetchall():
        dois.add(link[0])
    
    return dois

def get_doai_oa(doi):
    """ Given a DOI, return DOAI target URL if open access, None otherwise. """

    doaiurl = 'http://doai.io/%s' % doi
    doai = session.head(url=doaiurl)
    if doai.status_code == 302:
        url = doai.headers['Location']
        if re.search('//dx.doi.org', url):
            return None
        else:
            return url
    
if __name__ == "__main__":
    main()
