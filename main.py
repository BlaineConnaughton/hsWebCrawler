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
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue
from bs4 import BeautifulSoup as bs
from google.appengine.ext import db

class SessionScraped(db.Model):
    ran_on = db.DateTimeProperty(required=True,auto_now_add=True)
    domainurl = db.StringProperty(required=True)


class ScrapedUrl(db.Model):

    url = db.StringProperty(required=True)
    ran_on = db.DateTimeProperty(required=True,auto_now_add=True)
    domainurl = db.StringProperty(required=True)
    url_content = db.TextProperty()
    session = db.ReferenceProperty(SessionScraped , collection_name='urls')

    def created(self):
        return format_date(self.ran_on)

    def scrapedurlgetall():
        q = ScrapedUrl.all()
        data = q.fetch(10)

def get_urls(url , domain):

    data = memcache.get(url)
    #if we haven't seen this url before, add it then go do processing, if we have, exit
    if data is None:
        memcache.add(url, url, 3600)
    else:
        return

    response = urlfetch.get(url)

    soup = bs.BeautifulSoup(response.content)

    for link in soup.findAll('a'):
        #check to see if the links are on the domain we started with, if they are not, probably don't need to analyze
        domain_check = str(link)

        #if data is None and it passes domain check, add it to the task queue
        if data == None and domain_check.find(domain) != -1:


            #update table
            db = ScrapedUrl()
            db.url = link
            db.domainurl = domain
            #db.session = mysession
            db.put()

            #create api point to make this request again
            taskqueue.add(url='/api/approval/publish', params={ 'url': link.get('href') , 'domain': domain})

    return crawled

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('Hello world!')

    def post(self):
        url = self.request.get('url')
        domain = self.request.get('domain')
        get_urls(url=url , domain=domain)
        return 'Eagle has landed'


app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
