#!/usr/bin/env python
#coding=utf-8

import hashlib
import os
import time,datetime
import re
import urllib
import string
import uuid
import socket
import urllib2
from urllib import quote_plus

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

import feedparser
from tornado import template
from tornado import escape
from BeautifulSoup import BeautifulSoup
from selector import HtmlXPathSelector

try:
    from tornado import httpclient
except:
    httpclient = None
   
import encodings
encodings.aliases.aliases['gb2312'] = 'gb18030'
encodings.aliases.aliases['gbk'] 	= 'gb18030'

iswindows = 'win32' in sys.platform.lower() or 'win64' in sys.platform.lower()
isosx     = 'darwin' in sys.platform.lower()
isfreebsd = 'freebsd' in sys.platform.lower()
islinux   = not(iswindows or isosx or isfreebsd)

if iswindows:
    kindlegen = os.path.join(os.path.dirname(__file__), 'kindlegen.exe')
else:
    kindlegen = os.path.join(os.path.dirname(__file__), 'kindlegen')
    
data_dir = os.path.abspath(os.path.dirname(__file__))

BOOK_TEMPLATE = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"> 
    <title>{{ title }}</title>
    <style type="text/css">
    body{
        font-size: 1.1em;
        margin:0 5px;
    }

    h1{
        font-size:4em;
        font-weight:bold;
    }

	h2 {
		font-size: 1.2em;
		font-weight: bold;
		margin:0;
	}
	a {
		color: inherit;
		text-decoration: inherit;
		cursor: default
	}
	a[href] {
		color: blue;
		text-decoration: underline;
		cursor: pointer
	}
	p{
        text-indent:1.5em;
        line-height:1.5em;
        margin-top:0;
        margin-bottom:0;
    }
	.italic {
		font-style: italic
    }
	#cover{
        text-align:center;
    }
    #toc{
        page-break-after: always;
    }
    #content{
        margin-top:10px;
        page-break-after: always;
    }
    </style>
</head>
<body>
	<div id="cover">
        <img src="cover.jpg" />
        <h1 id="title">{{ title }}</h1>
        {{ create_time }}<br />
        <small><a href="http://dogear.mobi/">dogear.mobi</a></small>
	</div>
	<mbp:pagebreak/>
	<div id="toc">
		<h2>Table of Contents</h2>
		<ol>
		{% for entry in entries %}
			<li>
				<a href="#entry{{ entry['index'] }}">{{ entry['title'] }}</a>
				{% if entry['updated'] %}
				<small class="last_updated">[{{ entry['updated'] }}]</small>
				{% end %}
			</li>
		{% end %}
		</ol>
	</div>
	<mbp:pagebreak/>
	<div id="content">
    {% for entry in entries %}
    <div id="entry{{ entry['index'] }}" class="entry">
        <h2>
            <a href="{{ entry['link'] }}">{{ entry['title'] }}</a>
            <small class="italic">{{ entry['updated'] }}</small>
        </h2>
        
        <div base="{{ entry['base'] }}" class="entry_content">
            {{ entry['summary'] }}
        </div>
    </div>
    {% end %}
	</div>
</body>
</html>
"""

NCX_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="zh-CN">
<head>
<meta name="dtb:uid" content="{{ uuid }}"/>
<meta name="dtb:depth" content="4"/>
<meta name="dtb:totalPageCount" content="0"/>
<meta name="dtb:maxPageNumber" content="0"/>
</head>
<docTitle><text>{{ title }}</text></docTitle>
<docAuthor><text>dogear.in</text></docAuthor>
<navMap>
    <navPoint class="periodical">
        <navLabel><text>dogear feeds</text></navLabel>
        <content src="content.html"/>
        <content src="content_.html"/>
        <navPoint class="section">
            <navLabel><text>{{ title }}</text></navLabel>
            <content src="content.html"/>
            {% for entry in entries %}
            <navPoint class="article" id="article{{ entry['index'] }}" playOrder="{{ entry['index'] }}">
              <navLabel><text>{{ entry['title'] }}</text></navLabel>
              <content src="content.html#entry{{ entry['index'] }}"/>
            </navPoint>
            {% end %}
        </navPoint>
    </navPoint>
</navMap>
</ncx>
"""

OPF_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="uid">
<metadata>
<dc-metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:title>Dogear Feeds</dc:title>
    <dc:language>zh-CN</dc:language>
    <dc:identifier id="uid">{{ uuid }}</dc:identifier>
    <dc:creator>dogear.mobi</dc:creator>  
    <dc:publisher>dogear.mobi</dc:publisher>
    <dc:subject>Dogear Feeds</dc:subject>
    {% set date_format = "%Y-%m-%dT%H:%M:%SZ" %}
    <dc:date>{{ datetime.datetime.utcnow().strftime(date_format) }}</dc:date>
    <dc:description></dc:description>
</dc-metadata>
<x-metadata>
<output encoding="utf-8" content-type="application/x-mobipocket-subscription-magazine"></output>
</output>
<EmbeddedCover>cover.jpg</EmbeddedCover>
</x-metadata>
<meta name="title" content="my-cover-image" />
</metadata>
<manifest>
    <item id="content" media-type="application/xhtml+xml" href="content.html"></item>
    <item id="toc" media-type="application/x-dtbncx+xml" href="toc.ncx"/>
    <item href="cover.jpg" id="my-cover-image" media-type="image/jpeg" />
</manifest>
	
<spine toc="toc">
    <itemref idref="content"/>
</spine>

<guide>
	<reference type="text" title="beginning" href="content.html#content" />
	<reference type="toc" title="toc" href="content.html#toc"></reference>
	<reference type="text" title="cover" href="content.html#cover"></reference>
</guide>
</package>
"""

class Feed2mobi:
    
    remove_tags = [
            dict(name='object'),
            dict(name='video'),
            dict(name='input'),
            dict(name='button'),
            #dict(name='hr'),
            #dict(name='img')
        ]
    
    remove_attributes = ['class','id','title', 'style']
    no_image = False
    max_image_number = 10
    
    def __init__(self, url, xpath=False, timeout=30):
        self.url = url
        self.xpath = xpath
         
        self.data_dir = os.path.join(data_dir, hashlib.sha1(quote_plus(self.url)).hexdigest())
        if os.path.isdir(self.data_dir) is False:
            os.makedirs(self.data_dir, 0777)
            
        if os.path.isdir(self.data_dir+'images/') is False:
            os.makedirs(self.data_dir+'images/', 0777)
            
        socket.setdefaulttimeout(timeout)

    def create_file(self, tpl, outfile):
        t = template.Template(tpl)
        content = t.generate(
            uuid = uuid.uuid1(), #uuid3(uuid.NAMESPACE_DNS, self.url),
            no_image = self.no_image,
            title = self.feed.feed.title,
            #subtitle = self.feed.feed.subtitle,
            logo_image = self.logo_image,
            entries = self.entries,
            max_index = self.max_index,
            #updated = time.strftime('%Y-%m-%d',self.feed.feed.updated_parsed),
            #info = self.feed.feed.info,
            #author = self.feed.feed.author
            create_time = time.strftime('%Y-%m-%d %H:%M'),
            create_date = time.strftime('%m-%d')
        )
        
        outfile = self.data_dir+outfile
        
        fp = open(outfile, 'wb')
        fp.write(content)
        fp.close()
    
    def down_image(self, url, referer=None):
        url = escape.utf8(url)
        image_guid = hashlib.sha1(url).hexdigest()
        
        x = url.split('.')
        
        ext = None
        if len(x) > 1:
            ext = x[-1]
            
            if len(ext) > 4:
                ext = ext[0:3]
                
            ext = re.sub('[^a-zA-Z]','', ext)
            ext = ext.lower()
            
            if ext not in ['jpg', 'jpeg', 'gif','png','bmp']:
                return False
        else:
            return False

        filename = 'images/' + image_guid + '.' + ext
        fullname = self.data_dir + filename
        
        if os.path.isfile(fullname) is False:
            #try:
            #    urllib.urlretrieve(url, fullname)
            #except:
            #    return False
            try:                
                req = urllib2.Request(url)
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.99 Safari/533.4')
                req.add_header('Accept-Language', 'zh-cn,zh;q=0.7,nd;q=0.3')
                req.add_header('Referer', referer)
                response = urllib2.urlopen(req)
                
                localFile = open(fullname, 'wb')
                localFile.write(response.read())
                
                response.close()
                localFile.close()
                
            except Exception, e: # IOError, e:
                return False

        return filename
    
    def get_fulltext(self, url, xpath):
        
        try:
            req = urllib2.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.99 Safari/533.4')
            req.add_header('Accept-Language', 'zh-cn,zh;q=0.7,nd;q=0.3')
            response = urllib2.urlopen(req)
            
            html = response.read()
            html = BeautifulSoup(html).renderContents('utf-8')
            hxs = HtmlXPathSelector(html)
            
            content = hxs.select(xpath).extract()
            
            content = ''.join(content)
            return content
        except:
            return False
        
    def parse_summary(self, summary, link):
        
        #summary = escape.utf8(summary)
        soup = BeautifulSoup(summary)
        
        for span in list(soup.findAll(attrs={"class" : "MASSb0759798486b"})):
            span.extract()
        
        for script in list(soup.findAll('script')):
            script.extract()
            
        for o in soup.findAll(onload=True):
            del o['onload']
            
        for script in list(soup.findAll('noscript')):
            script.extract()
            
        for span in list(soup.findAll(attrs={ "style" : "display: none;" })):
            span.extract()
            
        for attr in self.remove_attributes:
            for x in soup.findAll(attrs={attr:True}):
                del x[attr]
                
        for tag in self.remove_tags:
            for x in soup.findAll(tag['name']):
                x.extract()
                
        for base in list(soup.findAll(['base', 'iframe'])):
            base.extract()
            
        #for p in list(soup.findAll(['p', 'div'])):
        #    p['style'] = 'text-indent:2em'
        
        img_count = 1
        for img in list(soup.findAll('img')):
            
            if self.no_image or img_count >= self.max_image_number:
                img.extract()
            else:
                image = self.down_image(img['src'], link)

                if image:
                    img['src'] = image
                else:
                    img.extract()
                    
            img_count = img_count + 1
        
        return soup.renderContents('utf-8')
        
    def parse(self):
        agent = 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.99 Safari/533.4'
        self.feed = feedparser.parse(self.url, agent=agent)
        return self
    
    def build(self,no_image=False):
        
        self.no_image = no_image
        
        if self.feed.bozo == 1:
            print self.feed.bozo_exception
            return False

        if 'image' in self.feed.feed and 'href' in self.feed.feed.image:
            self.logo_image = self.down_image(self.feed.feed.image.href, self.url)
        else:
            self.logo_image = False
        
        index,entries = 1,[]
        for entry in self.feed.entries:
            
            if self.xpath:
                print "get fulltext"
                fulltext = self.get_fulltext(entry.link, self.xpath)
                
                if fulltext:
                    entry.summary = fulltext
            
            try:
                content = entry.content
                
                if content:
                    entry.summary = content
            except:
                pass
            
            summary =  self.parse_summary(entry.summary, entry.link)
            
            if 'guid' not in entry or not entry.guid:
                entry.guid = entry.link
            
            entries.append({
                    'link':entry.link,
                    'title':entry.title,
                    'updated':time.strftime('%Y-%m-%d %H:%M:%S',entry.updated_parsed),
                    'summary':summary,
                    'base':entry.summary_detail.base,
                    'index':index
                })
            index = index + 1
    
        self.max_index = index
        self.entries = entries
        
        self.create_file(BOOK_TEMPLATE, 'content.html')
        
        #self.create_file(BOOK_TEMPLATE, 'content_.html')
        #self.create_file(TOC_TEMPLATE, 'toc.html')
        self.create_file(NCX_TEMPLATE, 'toc.ncx')
        #self.create_file(INDEX_TEMPLATE, 'index.html')
        self.create_file(OPF_TEMPLATE, 'content.opf')
        
        if self.no_image:
            mobi_file = 'feed.mobi'
        else:
            mobi_file = 'feed.mobi'
        
        os.system('%s %s -c0 -o %s' % (kindlegen, self.data_dir+"content.opf", mobi_file))
        
        return self.data_dir+mobi_file

def main(id, url, xpath=False):
    feeder = Feed2mobi(url, xpath)
    feeder.max_image_number = 20
    print feeder.parse().build()
    
if __name__ == '__main__':
    main(300, 'http://www.cnbeta.com/backend.php')