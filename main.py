#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import logging
import json
import time
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue
from bs4 import BeautifulSoup as bs
from google.appengine.ext import db


class SessionScraped(db.Model):
    ran_on = db.DateTimeProperty(required=True,auto_now_add=True)
    domainurl = db.StringProperty()

    @staticmethod
    def get_all(count=None):
        q = SessionScraped.all()
        data = q.fetch(count)
        return data


class ScrapedUrl(db.Model):

    url = db.StringProperty()
    ran_on = db.DateTimeProperty(required=True,auto_now_add=True)
    domainurl = db.StringProperty()
    url_content = db.TextProperty()
    session = db.ReferenceProperty(SessionScraped , collection_name='urls')

    def created(self):
        return format_date(self.ran_on)

    @staticmethod
    def get_all(count=None):
        q = ScrapedUrl.all()
        data = q.fetch(count)
        return data

def bump_counter(url):
    client = memcache.Client()

    while True: # Retry loop
        counter = client.gets(url)
        assert counter is not None, 'Uninitialized counter'
        if client.cas(url, counter+1):
            break

def get_urls(url , mysession):

    logging.warning('1')
    client = memcache.Client()

    data = client.gets(url)
    #if we haven't seen this url before, add it then go do processing, if we have, exit
    if data == None:
        memcache.set(url , 1)
    elif data >= 2:
        return

    bump_counter(url)

    response = urlfetch.fetch(url)

    soup = bs(response.content)

    for link in soup.findAll('a'):
        if link.get('href') <> None:
            #check to see if the links are on the domain we started with, if they are not, probably don't need to analyze
            domain_check = str(link)

            data = client.gets(link.get('href'))

            #if data is None and it passes domain check, add it to the task queue
            if domain_check.find(str(mysession.domainurl)) != -1 and data == None:
                memcache.set(link.get('href') , 1)

                #double check that we haven't already scraped this from a different queue
                querystring = "SELECT * FROM ScrapedUrl WHERE url = " + "'" + link.get('href') + "'"
                query = db.GqlQuery(querystring)

                if query.count() == 0:
                    #update table
                    database = ScrapedUrl(domainurl=mysession.domainurl , url=link.get('href'))
                    database.session = mysession
                    database.put()

                    #queue api point to make this request again
                    params={ 'url': link.get('href') , 'session': mysession.key().id()}
                    taskqueue.add(url='/api', params=params)

    return

class TestHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('<h1>Your request</h1>')
        self.response.out.write(self.request)
        self.response.out.write('<h2>Your q value</h2>')
        self.response.out.write(self.request.get('q'))

class GetURLHandler(webapp2.RequestHandler):
    def post(self):
        url = self.request.get('url')
        sessionid = self.request.get('session')

        session = SessionScraped.get_by_id(int(sessionid))

        get_urls(url=url , mysession=session)


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write("Scrape this endpoint")

    def post(self):
        url = self.request.get('url')
        domain = self.request.get('domain')

        session = SessionScraped()
        session.domainurl = domain
        session.put()

        surl = ScrapedUrl()
        surl.put()

        get_urls(url=url , mysession=session)


app = webapp2.WSGIApplication([
    ('/', MainHandler) , ('/api', GetURLHandler) ,  ('/test', TestHandler)
], debug=True)




