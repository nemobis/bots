from TwitterAPI import TwitterAPI
import codecs
import time

APP_KEY = 'abc'
APP_SECRET = 'def'
APP_TOKEN = 'ghi'
APP_ACCESS = 'lmn'
api = TwitterAPI(APP_KEY, APP_SECRET, APP_TOKEN, APP_ACCESS)

with codecs.open('lista.txt', 'r', encoding='utf-8') as lista:
    for listando in lista.readlines():
        r = api.request('lists/members/create',
                {'slug': 'scuola', 'owner_screen_name': 'WikimediaItalia', 'screen_name': listando } )

        if r.status_code > 200:
            print(u"ERROR with: %s" % listando)
            print r.text
        time.sleep(1)
