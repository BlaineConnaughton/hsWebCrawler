#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      bconnaughton
#
# Created:     06/12/2013
# Copyright:   (c) bconnaughton 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import urlfetch
import BeautifulSoup as bs
import json

def main():
    pass

if __name__ == '__main__':
    main()

##def get_urls(url2 , domain):
##
##    to_crawl = []
##    crawled = []
##
##    response = urlfetch.get(url2)
##
##    soup = bs.BeautifulSoup(response.content)
##
##    for link in soup.findAll('a'):
##        to_crawl.append((link.get('href')))
##
##    return to_crawl


def get_urls(url , domain):

    crawled = []
    crawled.append(url)
    #this needs to be replaced with an update to memcache

    response = urlfetch.get(url)

    soup = bs.BeautifulSoup(response.content)

    for link in soup.findAll('a'):

        domain_check = str(link)
        #will need to check memcache
        if link.get('href') not in crawled and domain_check.find(domain) != -1:

            #create api point to make this request again
            crawled += get_urls(link.get('href') , domain)
            #update table

    return crawled