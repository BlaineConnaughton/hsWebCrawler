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

##def get_urls(url , domain):
##
##    to_crawl = []
##    crawled = []
##
##    response = urlfetch.get(url)
##
##    soup = bs.BeautifulSoup(response.content)
##
##    for link in soup.findAll('a'):
##        to_crawl.append(link)
##
##    return to_crawl


def get_urls(url2 , domain):

    to_crawl = []
    crawled = []

    response = urlfetch.get(url2)

    soup = bs.BeautifulSoup(response.content)

    for link in soup.findAll('a'):

        if link not in crawled and link.find(domain) <> -1:
            strlink = str(link)
            to_crawl = to_crawl + get_urls(strlink, domain)
            crawled.append(link.get('href'))
        else:
            to_crawl.append(link)

    return to_crawl