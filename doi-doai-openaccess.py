#!/usr/bin/env python
# -*- coding: utf-8  -*-
"""
Queries the Wikimedia projects database replica on labsdb to list all
links to DOI documents which are Open Access on DOAI and Dissem.in.
Requires Wikimedia Labs labsdb local access.

Usage:
    doi-doai-openaccess.py --help
    doi-doai-openaccess.py [--depositable] [--oadoi] [--dbcnf=DBCNF]
    [--list=FILE | <dbname>] [--download] [--export]

Options:
    --help           Prints this documentation.
    --depositable    Lists closed access DOIs which could be deposited.
    --download       Download the PDF from the OA URL retrieved from oaDOI.
    --oadoi          Use the Unpaywall (oaDOI) API instead of DOAI.
    --export         Write a CSV with the OA URLs to dois.csv or [list].csv.
    --list=FILE      Reads the DOIs from a text file rather than the database.
    --dbcnf=DBCNF    The configuration file with credentials
                     [default: ~/.my.cnf]
    <dbname>         The dbname of the wiki to search DOIs in
                     [default: enwiki].

Copyright waived (CC-0), Federico Leva, 2016–2017
"""

from __future__ import absolute_import, division, print_function, \
                       unicode_literals

import os
import random
import re
import sys
import time
from contextlib import contextmanager
from codecs import open
try:
    import unicodecsv as csv
except ImportError:
    import csv as csv
import docopt
import requests
import requests.exceptions
import urllib3.exceptions
try:
    import pymysql as dbclient
except ImportError:
    print('WARNING: No pymysql, cannot query the DB')

if sys.version_info >= (3,):
    from urllib.parse import unquote, quote_plus
else:
    from urllib import unquote, quote_plus

SESSION = requests.Session()
SESSIONDOAI = requests.Session()
try:
    from requests.packages.urllib3.util.retry import Retry
    from requests.adapters import HTTPAdapter
    # Courtesy datashaman https://stackoverflow.com/a/35504626
    __retries__ = Retry(total=5,
                        backoff_factor=2,
                        status_forcelist=[500, 502, 503, 504])
    SESSION.mount('https://', HTTPAdapter(max_retries=__retries__))
    SESSION.mount('http://', HTTPAdapter(max_retries=__retries__))
except:
    # Our urllib3/requests is too old
    pass


@contextmanager
def get_connection(wiki, dbcnf):
    """ Create a connection object to a database:
        * dbname: {wiki}.labsdb
        * hostname: {wiki}_p
        * default_file: {dbcnf}
    """

    if sys.version_info >= (3,):
        # https://bugs.mysql.com/bug.php?id=84389
        connection = dbclient.connect(host=wiki + '.labsdb',
                                      db=wiki + '_p',
                                      read_default_file=dbcnf)
        # connection is <class 'pymysql.connections.Connection'>

    else:
        connection = dbclient.connect(host=wiki + '.labsdb',
                                      db=wiki + '_p',
                                      read_default_file=dbcnf)
        # connection is <class 'MySQLdb.connections.Connection'>

    assert isinstance(connection, dbclient.connections.Connection)

    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()
    finally:
        connection.close()


def main(argv=None):
    """ Queries the Wikimedia projects database replica on labsdb to list all
        links to DOI documents which are Open Access on DOAI and Dissem.in.
    """
    args = docopt.docopt(__doc__, argv=argv)

    # default does not seem to work properly
    if args['<dbname>'] is None:
        args['<dbname>'] = 'enwiki'

    wiki = args['<dbname>']
    dbcnf = os.path.abspath(os.path.expanduser(args['--dbcnf']))

    if args['--list']:
        doilist = open(args['--list'], 'r', encoding='utf-8').readlines()
    else:
        doilist = get_doi_el(wiki, dbcnf).union(get_doi_iwl(wiki, dbcnf))

    if args['--export']:
        export = open((args['--list'] or 'dois') + '.csv', 'a')
        writer = csv.writer(export,
                            delimiter='\t',
                            lineterminator='\n')
        writer.writerow([u'DOI', u'best_oa_location', u'host_type'])

    if args['--depositable'] and not args['--oadoi']:
        for doi in doilist:
            doi = doi.strip()
            try:
                archived = get_dissemin_pdf(doi)
                if archived:
                    print(u"URL available for DOI: {}".format(doi))
                else:
                    archived = get_doai_oa(doi)
                    if archived:
                        if re.search('academia.edu', archived):
                            print(u"Social URL available for DOI: {}"
                                  .format(doi))
                            archived = None
                        else:
                            print(u"URL available for DOI: http://doai.io/{}"
                                  .format(doi))

                if not archived and is_depositable(doi):
                    print(u"Depositable DOI: {}".format(doi))
                else:
                    print(u"Non-depositable DOI: {}".format(doi))
            except:
                continue
    elif args['--depositable'] and args['--oadoi']:
        for doi in doilist:
            try:
                doi = doi.strip()
                if get_oadoi(doi):
                    print(u"URL available in oaDOI for DOI: {}".format(doi))
                else:
                    if is_depositable(doi):
                        print(u"Depositable DOI: {}".format(doi))
                    else:
                        print(u"Non-depositable DOI: {}".format(doi))
            except:
                continue
    else:
        for doi in doilist:
            doi = doi.strip()
            if args['--oadoi']:
                pdf, host_type = get_oadoi(doi)
                if pdf:
                    print(doi)
                    if args['--download']:
                        get_doi_download(doi, pdf)
                    if args['--export']:
                        writer.writerow([doi, pdf, host_type])
            else:
                if args['--download']:
                    get_doi_download_fatcat(doi)
                else:
                    get_doai_oa(doi)
                    print(doi)

        if args['--export']:
            export.close()


def get_doi_el(wiki, dbcnf):
    """ Set of DOI codes from external links. """

    dois = set([])

    doiquery = """SELECT el_to
    FROM externallinks
    WHERE el_index LIKE 'https://org.doi.dx./10%'
    OR el_index LIKE 'http://org.doi.dx./10%'"""

    with get_connection(wiki, dbcnf) as connection:
        cursor = connection.cursor()
        cursor.execute(doiquery)
        for link in cursor.fetchall():
            try:
                doi = re.findall('10.+$', link[0].decode('utf-8'))[0]
                if doi:
                    dois.add(unquote(doi))
            except IndexError:
                continue

    # print "Found %d DOI external links on %s" % (len(dois), wiki)
    return dois


def get_doi_iwl(wiki, dbcnf):
    """ Set of DOI codes from interwiki links. """

    dois = set([])

    doiquery = """SELECT iwl_title
    FROM iwlinks
    WHERE iwl_prefix = 'doi'
    AND iwl_title LIKE '10%'"""

    with get_connection(wiki, dbcnf) as connection:
        cursor = connection.cursor()
        cursor.execute(doiquery)
        for link in cursor.fetchall():
            dois.add(link[0])

    return dois


def get_doai_oa(doi):
    """ Given a DOI, return DOAI target URL if green open access,
        None otherwise.
    """

    doaiurl = 'http://doai.io/{}'.format(doi)
    try:
        doai = SESSIONDOAI.head(url=doaiurl)
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
    """ Given a DOI, return oaDOI target URL if open access,
        None otherwise.
    """

    try:
        oadoi = SESSIONDOAI.get("http://api.unpaywall.org/v2/{}"
                                "?email=openaccess@wikimedia.it"
                                .format(doi))
        oadoi = oadoi.json()['best_oa_location']
    except:
        time.sleep(random.randint(1, 100))
        return False

    if oadoi:
        if oadoi['url_for_pdf']:
            return oadoi['url_for_pdf'], oadoi['host_type']
        else:
            return oadoi['url'], oadoi['host_type']
    else:
        return None, None


def get_dissemin_pdf(doi):
    """ Given a DOI, return the first URL which Dissemin believes to provide
        a PDF
    """

    try:
        req = SESSION.get('https://dissem.in/api/%s' % doi)
        if req.status_code >= 400:
            return None
        for record in req.json()['paper']['records']:
            if 'pdf_url' in record:
                return record['pdf_url']
    except:
        return

    return


def get_doi_download(doi, url):
    """ Given an URL, download the PDF and save in current directory. """
    try:
        with open("{}.pdf".format(quote_plus(doi)), 'wb') as out:
            req = SESSION.get(url, timeout=10)
            if req.status_code == 200 and req.headers['Content-Type'] == 'application/pdf':
                out.write(req.content)
            else:
                return False
    except requests.exceptions.ConnectionError:
        return None
    except urllib3.exceptions.MaxRetryError:
        return False
    except requests.exceptions.RetryError:
        return False
    except UnicodeError:
        # UnicodeDecodeError: 'utf-8' codec can't decode byte ...: invalid continuation byte
        return None

def get_doi_download_fatcat(doi):
    """ Given a DOI, download the PDF from fatcat and save in current directory. """
    try:
        req = SESSION.head("https://fatcat.wiki/release/lookup?doi={}".format(doi), timeout=2)
        fatcatid = req.headers['Location'].split('/')[-1]
        fatcat = SESSION.get("https://api.fatcat.wiki/v0/release/{}?expand=files".format(fatcatid), timeout=2)
        for copy in fatcat.json()['files']:
            if copy['mimetype'] != "application/pdf":
                continue
            for location in copy['urls']:
                if location['rel'] == "webarchive" or location['rel'] == "repository":
                    print("Found DOI: {} at URL: {}".format(doi, location['url']))
                    pdf = SESSION.get(location['url'], timeout=10)
                    if pdf.headers['Content-Type'] == 'application/pdf':
                        out = open("{}.pdf".format(quote_plus(doi)), 'wb')
                        out.write(pdf.content)
                        out.close()
                        return True
        return None
    except KeyError:
        return None
    except requests.exceptions.ConnectionError:
        return None
    except urllib3.exceptions.MaxRetryError:
        return False
    except requests.exceptions.RetryError:
        return False

def is_depositable(doi):
    # JSON requires 2.4.2
    # http://docs.python-requests.org/en/master/user/quickstart/#more-complicated-post-requests
    payload = '{{ "doi": "{}" }}'.format(doi)
    req = SESSION.post('https://dissem.in/api/query', data=payload)
    if req.status_code >= 400:
        print(u"ERROR with: {}".format(doi))
        return None
    try:
        dis = req.json()
        return dis['status'] == "ok" and 'classification' in dis['paper'] \
            and (dis['paper']['classification'] == "OK" or
                 dis['paper']['classification'] == "OA")
    except:
        return None

if __name__ == "__main__":
    main()
