#!/usr/bin/python
# -*- coding: ISO-8859-15 -*-
# =============================================================================
# Copyright (c) 2008 Tom Kralidis
#
# Authors : Tom Kralidis <tomkralidis@hotmail.com>
#
# Contact email: tomkralidis@hotmail.com
# =============================================================================

from owslib.etree import etree
import urlparse, urllib2
from urllib2 import urlopen, HTTPError
from StringIO import StringIO

"""
Utility functions and classes
"""

class RereadableURL(StringIO,object):
    """ Class that acts like a combination of StringIO and url - has seek method and url headers etc """
    def __init__(self, u):
        #get url headers etc from url
        self.headers = u.headers                
        #get file like seek, read methods from StringIO
        content=u.read()
        super(RereadableURL, self).__init__(content)


class ServiceException(Exception):
    #TODO: this should go in ows common module when refactored.  
    pass


def openURL(url_base, data, method='Get'):
    ''' function to open urls - wrapper around urllib2.urlopen but with additional checks for OGC service exceptions and url formatting'''
    url_base.strip() 
    lastchar = url_base[-1]
    if lastchar not in ['?', '&']:
        if url_base.find('?') == -1:
            url_base = url_base + '?'
        else:
            url_base = url_base + '&'
    try:
        if method == 'Post':
            u=urlopen(url_base,  data)
        else:
            u=urlopen(url_base + data)
    except HTTPError, e: #Some servers may set the http header to 400 if returning an OGC service exception.
        if e.code == 400:
            raise ServiceException, e.read()

    # check for service exceptions without the http header set
    if u.info()['Content-Type'] in ['text/xml', 'application/xml']:          
        #just in case 400 headers were not set, going to have to read the xml to see if it's an exception report.
        #wrap the url stram in a extended StringIO object so it's re-readable
        u=RereadableURL(u)      
        se_xml= u.read()
        se_tree = etree.fromstring(se_xml)
        serviceException=se_tree.find('{http://www.opengis.net/ows}Exception')
        if serviceException is None:
            serviceException=se_tree.find('ServiceException')
        if serviceException is not None:
            raise ServiceException, \
            str(serviceException.text).strip()
        u.seek(0) #return cursor to start of u      
    return u

def nspath(path, ns=None):
    """

    Prefix the given path with the given namespace identifier.
    
    Parameters
    ----------

    - path: ElementTree API Compatible path expression
    - ns: the XML namespace URI.

    """

    if ns is None or path is None:
        return -1

    components = []
    for component in path.split('/'):
        if component != '*':
            component = '{%s}%s' % (ns, component)
        components.append(component)
    return '/'.join(components)

def testXMLValue(val, attrib=False):
    """

    Test that the XML value exists, return val.text, else return None

    Parameters
    ----------

    - val: the value to be tested

    """

    if val is not None:
        if attrib == True:
            return val
        else:
            return val.text
    else:
        return None


def http_post(url=None, request=None, lang='en-US'):
    """

    Invoke an HTTP POST request 

    Parameters
    ----------

    - url: the URL of the server
    - request: the request message
    - lang: the language

    """

    if url is not None:
        u = urlparse.urlsplit(url)
        r = urllib2.Request(url, request)
        r.add_header('User-Agent', 'OWSLib (http://trac.gispython.org/lab/wiki/OwsLib)')
        r.add_header('Content-type', 'text/xml')
        r.add_header('Content-length', '%d' % len(request))
        r.add_header('Accept', 'text/xml')
        r.add_header('Accept-Language', lang)
        r.add_header('Accept-Encoding', 'gzip,deflate')
        r.add_header('Host', u.netloc)
        up = urllib2.urlopen(r)
        response = up.read()
        up.close()
        return response
       
        
def xml2string(xml):
    """

    Return a string of XML object

    Parameters
    ----------

    - xml: xml string

    """
    return '<?xml version="1.0" encoding="ISO-8859-1" standalone="no"?>\n' + xml

def xmlvalid(xml, xsd):
    """

    Test whether an XML document is valid

    Parameters
    ----------

    - xml: XML content
    - xsd: pointer to XML Schema (local file path or URL)

    """

    xsd1 = etree.parse(xsd)
    xsd2 = etree.XMLSchema(xsd1)

    doc = etree.parse(StringIO.StringIO(xml))
    return xsd2.validate(doc)