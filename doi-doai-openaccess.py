#!/usr/bin/env python2
# -*- coding: utf-8  -*-
"""
Queries the Wikimedia projects database replica on labsdb to list all
links to DOI documents which are Open Access on DOAI and Dissem.in.
Requires Wikimedia Labs labsdb local access.

Usage:
    doi-doai-openaccess.py --help
    doi-doai-openaccess.py [--depositable] [--oadoi] [--list=FILE | <dbname>]

Options:
    --help           Prints this documentation.
    --depositable    Lists closed access DOIs which could be deposited.
    --oadoi          Use the oaDOI API instead of DOAI.
    --list=FILE      Reads the DOIs from a text file rather than the database.
    <dbname>         The dbname of the wiki to search DOIs in [default: enwiki].

Copyright waived (CC-0), Federico Leva, 2016–2017
"""

import docopt
import json
try:
    import MySQLdb
except:
    print "WARNING: Cannot query the DB, MySQLdb isn't available"
import random
import re
import requests
import time
import urllib

session = requests.Session()
sessiondoai = requests.Session()
try:
    from requests.packages.urllib3.util.retry import Retry
    from requests.adapters import HTTPAdapter
    # Courtesy datashaman https://stackoverflow.com/a/35504626
    retries = Retry(total=5,
                    backoff_factor=2,
                    status_forcelist=[ 500, 502, 503, 504 ])
    session.mount('https://', HTTPAdapter(max_retries=retries))
except:
    # Our urllib3/requests is too old
    pass

def main(argv=None):

    args = docopt.docopt(__doc__, argv=argv)
    wiki = args['<dbname>']

    if args['--list']:
        doilist = open(args['--list'], 'r').readlines()
    else:
        doilist = get_doi_el(wiki) + get_doi_iwl(wiki)

    if args['--depositable'] and not args['--oadoi']:
        for doi in doilist:
            doi = doi.strip()
            try:
                archived = get_dissemin_pdf(doi)
                if archived:
                    print u"URL available for DOI: %s" % doi
                else:
                    archived = get_doai_oa(doi)
                    if archived:
                        if re.search('academia.edu', archived):
                            print u"Social URL available for DOI: %s" % doi
                            archived = None
                        else:
                            print u"URL available for DOI: http://doai.io/%s" % doi

                if not archived and is_depositable(doi):
                        print u"Depositable DOI: %s" % doi
                else:
                        print u"Non-depositable DOI: %s" % doi
            except:
                continue
    elif args['--depositable'] and args['--oadoi']:
        for doi in doilist:
            doi = doi.strip()
            if get_oadoi(doi):
                print u"URL available in oaDOI for DOI: %s" % doi
            else:
                if is_depositable(doi):
                    print u"Depositable DOI: %s" % doi
                else:
                    print u"Non-depositable DOI: %s" %doi
    else:
        for doi in doilist:
            if args['--oadoi']:
                if get_oadoi(doi):
                    print doi
            else:
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
        try:
            doi = re.findall('10.+$', link[0])[0]
            if doi:
                dois.add(urllib.unquote(doi))
        except IndexError:
            continue

    # print "Found %d DOI external links on %s" % (len(dois), wiki)
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
    """ Given a DOI, return DOAI target URL if green open access, None otherwise. """

    doaiurl = 'http://doai.io/%s' % doi
    try:
        doai = sessiondoai.head(url=doaiurl)
    except requests.ConnectionError:
        time.sleep(random.randint(1, 100))
        return False

    if doai.status_code == 302:
        url = doai.headers['Location']
        if re.search('doi.org', url):
            return None
        else:
            return url

def get_oadoi(doi):
    """ Given a DOI, return oaDOI target URL if open access, None otherwise. """

    try:
        oadoi = sessiondoai.get("https://api.oadoi.org/%s?email=openaccess@wikimedia.it" % doi)
        oadoi = oadoi.json()['results'][0]
    except:
        time.sleep(random.randint(1, 100))
        return False

    if 'free_fulltext_url' in oadoi:
        return oadoi['free_fulltext_url']
    else:
        return None

def get_dissemin_pdf(doi):
    """ Given a DOI, return the first URL which Dissemin believes to provide a PDF """

    r = session.get('https://dissem.in/api/%s' % doi)
    if r.status_code >= 400:
        return None
    try:
        for record in r.json()['paper']['records']:
            if 'pdf_url' in record:
                return record['pdf_url']
    except:
        return

    return

def is_depositable(doi):
    # JSON requires 2.4.2 http://docs.python-requests.org/en/master/user/quickstart/#more-complicated-post-requests
    payload = '{"doi": "%s"}' % doi
    r = session.post('https://dissem.in/api/query', data=payload)
    if r.status_code >= 400:
        print u"ERROR with: %s" % doi
        return None
    try:
        dis = r.json()
        if dis['status'] == "ok" and 'classification' in dis['paper'] and ( dis['paper']['classification'] == "OK" or dis['paper']['classification'] == "OA" ):
            return True
        else:
            return False
    except:
        return None

if __name__ == "__main__":
    main()
