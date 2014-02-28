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

    url = db.StringProperty(required=True)
    ran_on = db.DateTimeProperty(required=True,auto_now_add=True)
    domainurl = db.StringProperty(required=True)
    url_content = db.TextProperty()
    session = db.ReferenceProperty(SessionScraped , collection_name='urls')

    def created(self):
        return format_date(self.ran_on)

    @staticmethod
    def get_all(count=None):
        q = ScrapedUrl.all()
        data = q.fetch(count)
        return data

def get_urls(url , mysession):

    data = memcache.get(url)
    #if we haven't seen this url before, add it then go do processing, if we have, exit
    if data is None:
        memcache.add(url, url, 3600)
        logging.warning("Seen this url before  :  " + url)
    else:
        return

    response = urlfetch.fetch(url)

    soup = bs(response.content)

    for link in soup.findAll('a'):
        #check to see if the links are on the domain we started with, if they are not, probably don't need to analyze
        domain_check = str(link)
        #if data is None and it passes domain check, add it to the task queue
        if domain_check.find(str(mysession.domainurl)) != -1:
            #double check that we haven't already scraped this from a different queue
            data = memcache.get(link.get('href'))
            if data == None:
                #update table
                db = ScrapedUrl(domainurl=mysession.domainurl , url=link.get('href'))
                db.session = mysession
                db.put()

                #queue api point to make this request again
                params={ 'url': link.get('href') , 'session': mysession.key().id()}
                logging.warning("params :  " + str(params))
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

        get_urls(url=url , mysession=session)


app = webapp2.WSGIApplication([
    ('/', MainHandler) , ('/api', GetURLHandler) ,  ('/test', TestHandler)
], debug=True)




