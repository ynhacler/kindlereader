#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
KindleReader
Created by Jiedan<lxb429@gmail.com> on 2010-11-08.
"""

__author__ = ["Jiedan<lxb429@gmail.com>", "williamgateszhao<williamgateszhao@gmail.com>"]
__version__ = "0.6.4"

import sys
import os
import time
import hashlib
import re
import uuid
import string
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import parsedate_tz
from datetime import date, datetime, timedelta
import codecs
import ConfigParser
import getpass
import subprocess
import Queue, threading
import socket, urllib2, urllib
from lib import smtplib
from lib.tornado import escape
from lib.tornado import template
from lib.BeautifulSoup import BeautifulSoup
from lib.kindlestrip import SectionStripper
from lib import feedparser
try:
    from PIL import Image
except ImportError:
    Image = None

iswindows = 'win32' in sys.platform.lower() or 'win64' in sys.platform.lower()
isosx = 'darwin' in sys.platform.lower()
isfreebsd = 'freebsd' in sys.platform.lower()
islinux = not(iswindows or isosx or isfreebsd)
socket.setdefaulttimeout(20)
imgq = Queue.Queue(0)
feedq = Queue.Queue(0)
updated_feeds = []
feedlock = threading.Lock()

TEMPLATES = {}
TEMPLATES['content.html'] = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"> 
    <title>{{ user }}'s kindle reader</title>
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
        line-height:1.3em;
        margin-top:0;
        margin-bottom:0;
    }
    .italic {
        font-style: italic
    }
    .do_article_title{
        line-height:1.5em;
        page-break-before: always;
    }
    #cover{
        text-align:center;
    }
    #toc{
        page-break-before: always;
    }
    #content{
        margin-top:10px;
        page-break-after: always;
    }
    </style>
</head>
<body>
    <div id="cover">
        <h1 id="title">{{ user }}'s kindle reader</h1>
        <a href="#content">Go straight to first item</a><br />
        {{ mobitime.strftime("%m/%d %H:%M") }}
    </div>
    <div id="toc">
        <h2>Feeds:</h2> 
        <ol> 
            {% set feed_count = 0 %}
            {% set feed_idx=0 %}
            {% for feed in feeds %}
            {% set feed_idx=feed_idx+1 %}
            {% if len(feed['entries']) > 0 %}
            {% set feed_count = feed_count + 1 %}
            <li>
              <a href="#sectionlist_{{ feed_idx }}">{{ feed['title'] }}</a>
              <br />
              {{ len(feed['entries']) }} items
            </li>
            {% end %}
            
            {% end %}
        </ol> 
        
        {% set feed_idx=0 %}
        {% for feed in feeds %}
        {% set feed_idx=feed_idx+1 %}
        {% if len(feed['entries']) > 0 %}
        <mbp:pagebreak />
        <div id="sectionlist_{{ feed_idx }}" class="section">
            {% if feed_idx < feed_count %}
            <a href="#sectionlist_{{ feed_idx+1 }}">Next Feed</a> |
            {% end %}
            
            {% if feed_idx > 1 %}
            <a href="#sectionlist_{{ feed_idx-1 }}">Previous Feed</a> |
            {% end %}
        
            <a href="#toc">TOC</a> |
            {{ feed_idx }}/{{ feed_count }} |
            {{ len(feed['entries']) }} items
            <br />
            <h3>{{ feed['title'] }}</h3>
            <ol>
                {% for item in feed['entries'] %}
                <li>
                  <a href="#article_{{ feed_idx }}_{{ item['idx'] }}">{{ item['title'] }}</a><br/>
                  {% if item['published'] %}{{ item['published'] }}{% end %}
                </li>
                {% end %}
            </ol>
        </div>
        {% end %}
        {% end %}
    </div>
    <mbp:pagebreak />
    <div id="content">
        {% set feed_idx=0 %}
        {% for feed in feeds %}
        {% set feed_idx=feed_idx+1 %}
        {% if len(feed['entries']) > 0 %}
        <div id="section_{{ feed_idx }}" class="section">
        {% for item in feed['entries'] %}
        <div id="article_{{ feed_idx }}_{{ item['idx'] }}" class="article">
            <h2 class="do_article_title">
              {% if item['url'] %}
              <a href="{{ item['url'] }}">{{ item['title'] }}</a>
              {% else %}
              {{ item['title'] }}
              {% end %}
            </h2>
            {% if item['published'] %}{{ item['published'] }}{% end %}
            <div>{{ item['content'] }}</div>
        </div>
        {% end %}
        </div>
        {% end %}
        {% end %}
    </div>
</body>
</html>
"""

TEMPLATES['toc.ncx'] = """<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="zh-CN">
<head>
<meta name="dtb:depth" content="4" />
<meta name="dtb:totalPageCount" content="0" />
<meta name="dtb:maxPageNumber" content="0" />
</head>
<docTitle><text>{{ user }}'s kindle reader</text></docTitle>
<docAuthor><text>{{ user }}</text></docAuthor>
<navMap>
    {% if format == 'periodical' %}
    <navPoint class="periodical">
        <navLabel><text>{{ user }}'s kindle reader</text></navLabel>
        <content src="content.html" />
        {% set feed_idx=0 %}
        {% for feed in feeds %}
        {% set feed_idx=feed_idx+1 %}
        {% if len(feed['entries']) > 0 %}
        <navPoint class="section" id="{{ feed_idx }}">
            <navLabel><text>{{ escape(feed['title']) }}</text></navLabel>
            <content src="content.html#section_{{ feed_idx }}" />
            {% for item in feed['entries'] %}
            <navPoint class="article" id="{{ feed_idx }}_{{ item['idx'] }}" playOrder="{{ item['idx'] }}">
              <navLabel><text>{{ escape(item['title']) }}</text></navLabel>
              <content src="content.html#article_{{ feed_idx }}_{{ item['idx'] }}" />
              <mbp:meta name="description">{{ escape(item['stripped']) }}</mbp:meta>
              <mbp:meta name="author">{% if item['author'] %}{{ item['author'] }}{% end %}</mbp:meta>
            </navPoint>
            {% end %}
        </navPoint>
        {% end %}
        {% end %}
    </navPoint>
    {% else %}
    <navPoint class="book">
        <navLabel><text>{{ user }}'s kindle reader</text></navLabel>
        <content src="content.html" />
        {% set feed_idx=0 %}
        {% for feed in feeds %}
        {% set feed_idx=feed_idx+1 %}
        {% if len(feed['entries']) > 0 %}
            {% for item in feed['entries'] %}
            <navPoint class="chapter" id="{{ feed_idx }}_{{ item['idx'] }}" playOrder="{{ item['idx'] }}">
                <navLabel><text>{{ escape(item['title']) }}</text></navLabel>
                <content src="content.html#article_{{ feed_idx }}_{{ item['idx'] }}" />
            </navPoint>
            {% end %}
        {% end %}
        {% end %}
    </navPoint>
    {% end %}
</navMap>
</ncx>
"""

TEMPLATES['content.opf'] = """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="uid">
<metadata>
<dc-metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    {% if format == 'periodical' %}
    <dc:title>{{ user }}'s kindle reader</dc:title>
    {% else %}
    <dc:title>{{ user }}'s kindle reader({{ mobitime.strftime("%m/%d %H:%M") }})</dc:title>
    {% end %}
    <dc:language>zh-CN</dc:language>
    <dc:identifier id="uid">{{ user }}{{ datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") }}</dc:identifier>
    <dc:creator>kindlereader</dc:creator>
    <dc:publisher>kindlereader</dc:publisher>
    <dc:subject>{{ user }}'s kindle reader</dc:subject>
    <dc:date>{{ datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") }}</dc:date>
    <dc:description></dc:description>
</dc-metadata>
{% if format == 'periodical' %}
<x-metadata>
    <output encoding="utf-8" content-type="application/x-mobipocket-subscription-magazine"></output>
    </output>
</x-metadata>
{% end %}
</metadata>
<manifest>
    <item id="content" media-type="application/xhtml+xml" href="content.html"></item>
    <item id="toc" media-type="application/x-dtbncx+xml" href="toc.ncx"></item>
</manifest>

<spine toc="toc">
    <itemref idref="content"/>
</spine>

<guide>
    <reference type="start" title="start" href="content.html#content"></reference>
    <reference type="toc" title="toc" href="content.html#toc"></reference>
    <reference type="text" title="cover" href="content.html#cover"></reference>
</guide>
</package>
"""

class KRConfig():
    '''提供封装好的配置'''
    def __init__(self, configfile = None):
        config = ConfigParser.ConfigParser()
        
        try:
            config.readfp(codecs.open(configfile, "r", "utf-8-sig"))
        except:
            config.readfp(codecs.open(configfile, "r", "utf-8"))
        
        self.auto_exit = self.getauto_exit(config)
        self.thread_numbers = self.getthread_numbers(config)
        self.kindle_format = self.getkindle_format(config)
        self.timezone = self.gettimezone(config)
        self.grayscale = self.getgrayscale(config)
        self.kindlestrip = self.getkindlestrip(config)
        self.mail_enable = self.getmail_enable(config)
        self.mail_host = self.getmail_host(config)
        self.mail_port = self.getmail_port(config)
        self.mail_ssl = self.getmail_ssl(config)
        self.mail_from = self.getmail_from(config)
        self.mail_to = self.getmail_to(config)
        self.mail_username = self.getmail_username(config)
        self.mail_password = self.getmail_password(config)
        self.mail_overlay = self.getmail_overlay(config)
        self.user = self.getuser(config)
        self.max_items_number = self.getmax_items_number(config)
        self.max_image_per_article = self.getmax_image_per_article(config)
        self.max_old_date = self.getmax_old_date(config)
        self.feeds = self.getfeeds(config)
        self.kindlegen = self.find_kindlegen_prog()
        self.work_dir = self.getwork_dir()

    def getauto_exit(self, config = None):
        try:
            return int(config.get('general', 'auto_exit').strip())
        except:
            return 1
        
    def getthread_numbers(self, config = None):
        try:
            return int(config.get('general', 'thread_numbers').strip())
        except:
            return 5
        
    def getkindle_format(self, config = None):
        try:
            format = str(config.get('general', 'kindle_format').strip())
            if format in ['book', 'periodical']:
                return format
            else:
                return 'book'
        except:
            return 'book'
        
    def gettimezone(self, config = None):
        try:
            return timedelta(hours = (int(config.get('general', 'timezone').strip())))
        except:
            return timedelta(hours = 8)
        
    def getgrayscale(self, config = None):
        try:
            return int(config.get('general', 'grayscale').strip())
        except:
            return 0

    def getkindlestrip(self, config = None):
        try:
            return int(config.get('general', 'kindlestrip').strip())
        except:
            return 1
        
    def getmail_host(self, config = None):
        try:
            return str(config.get('mail', 'host').strip())
        except:
            return None

    def getmail_port(self, config = None):
        try:
            return int(config.get('mail', 'port').strip())
        except:
            return 25

    def getmail_ssl(self, config = None):
        try:
            return int(config.get('mail', 'ssl').strip())
        except:
            return 0
        
    def getmail_from(self, config = None):
        try:
            return str(config.get('mail', 'from').strip())
        except:
            return None

    def getmail_to(self, config = None):
        try:
            return str(config.get('mail', 'to').strip())
        except:
            return None

    def getmail_username(self, config = None):
        try:
            return str(config.get('mail', 'username').strip())
        except:
            return None
        
    def getmail_password(self, config = None):
        try:
            return str(config.get('mail', 'password').strip())
        except:
            return None

    def getmail_enable(self, config = None):
        try:
            return int(config.get('mail', 'mail_enable').strip())
        except:
            return 0
        
    def getmail_overlay(self, config = None):
        try:
            return int(config.get('mail', 'overlay').strip())
        except:
            return 0
        
    def getuser(self, config = None):
        try:
            return str(config.get('reader', 'username').strip())
        except:
            return "user"
        
    def getmax_items_number(self, config = None):
        try:
            return int(config.get('reader', 'max_items_number').strip())
        except:
            return 5
        
    def getmax_image_per_article(self, config = None):
        try:
            return int(config.get('reader', 'max_image_per_article').strip())
        except:
            return 10

    def getmax_old_date(self, config = None):
        try:
            return timedelta(int(config.get('reader', 'max_old_date').strip()))
        except:
            return timedelta(3)

    def getfeeds(self, config = None):
        try:
            feeds = [config.get("feeds", feeds_option).strip() for feeds_option in config.options("feeds")]
        except:
            feeds = []
        finally:
            return feeds

    def find_kindlegen_prog(self):
        '''find the path of kindlegen'''
        try:
            kindlegen_prog = 'kindlegen' + (iswindows and '.exe' or '')

            # search in current directory and PATH to find kinglegen
            sep = iswindows and ';' or ':'
            dirs = ['.']
            dirs.extend(os.getenv('PATH').split(sep))
            for dir in dirs:
                if dir:
                    fname = os.path.join(dir, kindlegen_prog)
                    if os.path.exists(fname):
                        # print fname
                        return fname
        except:
            return None
    
    def getwork_dir(self):
        try:
            return os.path.abspath(os.path.dirname(sys.argv[0]))
        except:
            return None

class feedDownloader(threading.Thread):
    '''多线程下载并处理feed'''
    
    remove_tags = ['script', 'object', 'video', 'embed', 'iframe', 'noscript', 'style']
    remove_attributes = ['class', 'id', 'title', 'style', 'width', 'height', 'onclick']
    
    def __init__(self, threadname):
        threading.Thread.__init__(self, name = threadname)
        
    def run(self):
        global feedq
        while True:
            i = feedq.get()
            feed_data, force_full_text = self.getfeed(i['feed'])
            if feed_data:
                self.makelocal(feed_data, i['feed_idx'], force_full_text)
            else:
                pass
            feedq.task_done()

    def getfeed(self, feed):
        """access feed by url"""
        force_full_text = 0
        try:
            if feed[0:4] == 'full':
                force_full_text = 1
                feed_data = self.parsefeed(feed[4:])
                if feed_data:
                    return feed_data, force_full_text
                else:
                    raise UserWarning("illegal feed:{}".format(feed))
            else:
                feed_data = self.parsefeed(feed)
                if feed_data:
                    return feed_data, force_full_text
                else:
                    raise UserWarning("illegal feed:{}".format(feed))
        except Exception, e:
            logging.error("fail:({}):{}".format(feed, e))
            return None, None
                        
    def parsefeed(self, feed, retires = 1):
        """parse feed using feedparser"""
        try:  # 访问feed，自动尝试在地址结尾加上或去掉'/'
            feed_data = feedparser.parse(feed.encode('utf-8'))
            if not feed_data.feed.has_key('title'):
                if feed[-1] == '/':
                    feed_data = feedparser.parse(feed[0:-1].encode('utf-8'))
                elif feed[-1] != '/':
                    feed_data = feedparser.parse((feed + '/').encode('utf-8'))
                if not feed_data.feed.has_key('title'):
                    raise UserWarning("read error")
                else:
                    return feed_data
            else:
                return feed_data
        except UserWarning:
            logging.error("fail({}): {}".format(feed, "read error"))
            return None
        except Exception, e:
            if retires > 0:
                logging.error("error({}): {} , retry".format(feed, e))
                return self.parsefeed(feed, retires - 1)  # 如果读取错误，重试一次
            else:
                logging.error("fail({}): {}".format(feed, e))
                return None

    def makelocal(self, feed_data, feed_idx, force_full_text = 0):
        '''生成解析结果'''
        global updated_feeds
        global feedlock
        
        try:
            local = {
                    'idx': feed_idx,
                    'entries': [],
                    'title': feed_data.feed['title'],
                    }
                
            item_idx = 1
            for entry in feed_data.entries:
                if item_idx > krconfig.max_items_number:
                    break
                        
                try:
                    published_datetime = datetime(*entry.published_parsed[0:6])
                except:
                    published_datetime = self.parsetime(entry.published)
                    
                if datetime.utcnow() - published_datetime > krconfig.max_old_date:
                    break
                    
                try:
                    local_author = entry.author
                except:
                    local_author = "null"
                        
                local_entry = {
                               'idx': item_idx,
                               'title': entry.title,
                               'published':(published_datetime + krconfig.timezone).strftime("%Y-%m-%d %H:%M:%S"),
                               'url':entry.link,
                               'author':local_author,
                            }
                    
                if force_full_text:
                    local_entry['content'], images = self.force_full_text(entry.link)
                else:
                    try:
                        local_entry['content'], images = self.parse_summary(entry.content[0].value, entry.link)
                    except:
                        local_entry['content'], images = self.parse_summary(entry.summary, entry.link)

                local_entry['stripped'] = ''.join(BeautifulSoup(local_entry['content'], convertEntities = BeautifulSoup.HTML_ENTITIES).findAll(text = True))[:200]
                            
                local['entries'].append(local_entry)
                for i in images:
                    imgq.put(i)
                item_idx += 1
                
            if len(local['entries']) > 0:
                if feedlock.acquire():
                    updated_feeds.append(local)
                    feedlock.release()
                else:
                    feedlock.release()
                logging.info("from feed{} update {} items.".format(feed_idx, len(local['entries'])))
            else:
                logging.info("feed{} has no update.".format(feed_idx))
        except Exception, e:
            logging.error("fail(feed{}): {}".format(feed_idx, e))

    def parsetime(self, strdatetime):
        '''尝试处理feedparser未能识别的时间格式'''
        try:
            # 针对Mon,13 May 2013 06:48:25 GMT+8这样的奇葩格式
            if strdatetime[-5:-2] == 'GMT':
                t = datetime.strptime(strdatetime[:-6], '%a,%d %b %Y %H:%M:%S')
                return (t - timedelta(hours = int(strdatetime[-2:-1])) + krconfig.timezone)
            # feedparser对非utc时间的支持有问题（Wes, 22 May 2013 13:54:00 +0800这样的）
            elif (strdatetime[-5:-3] == '+0' or strdatetime[-5:-3] == '-0') and strdatetime[-2:] == '00':
                a = parsedate_tz(strdatetime)
                t = datetime(*a[:6]) - timedelta(seconds = a[-1])
                return (t + krconfig.timezone)
            else:
                return (datetime.utcnow() + krconfig.timezone)
        except Exception, e:
            return (datetime.utcnow() + krconfig.timezone)
            
    def force_full_text(self, url):
        '''当需要强制全文输出时，将每个entry单独发给fivefilters'''
        logging.info("(force full text):{}".format(url))
        fulltextentry = self.parsefeed('http://ftr.fivefilters.org/makefulltextfeed.php?url=' + url)
        if fulltextentry:
            return self.parse_summary(fulltextentry.entries[0].summary, url)
        else:
            try:
                return self.parse_summary(entry.content[0].value, url)
            except:
                return self.parse_summary(entry.summary, url)

    def parse_summary(self, summary, ref):
        """处理文章内容，去除多余标签并处理图片地址"""

        soup = BeautifulSoup(summary)

        for span in list(soup.findAll(attrs = { "style" : "display: none;" })):
            span.extract()

        for attr in self.remove_attributes:
            for x in soup.findAll(attrs = {attr:True}):
                del x[attr]

        for tag in soup.findAll(self.remove_tags):
            tag.extract()

        img_count = 0
        images = []
        for img in list(soup.findAll('img')):
            if (krconfig.max_image_per_article >= 0  and img_count >= krconfig.max_image_per_article) \
                or img.has_key('src') is False :
                img.extract()
            else:
                try:
                    if img['src'].encode('utf-8').lower().endswith(('jpg', 'jpeg', 'gif', 'png', 'bmp')):
                        localimage, fullname = self.parse_image(img['src'])
                        # 确定结尾为图片后缀，防止下载非图片文件（如用于访问分析的假图片）
                        if os.path.isfile(fullname) is False:
                            images.append({
                                'url':img['src'],
                                'filename':fullname,
                                'referer':ref
                                })
                        if localimage:
                            img['src'] = localimage
                            img_count = img_count + 1
                        else:
                            img.extract()
                    else:
                        img.extract()
                except Exception, e:
                    logging.info("error: %s" % e)
                    img.extract()

        return soup.renderContents('utf-8'), images

    def parse_image(self, url, filename = None):
        """处理img标签的src并映射到本地文件"""
        url = escape.utf8(url)
        image_guid = hashlib.sha1(url).hexdigest()

        x = url.split('.')
        ext = 'jpg'
        if len(x) > 1:
            ext = x[-1]

            if len(ext) > 4:
                ext = ext[0:3]

            ext = re.sub('[^a-zA-Z]', '', ext)
            ext = ext.lower()

            if ext not in ['jpg', 'jpeg', 'gif', 'png', 'bmp']:
                ext = 'jpg'

        y = url.split('/')
        h = hashlib.sha1(str(y[2])).hexdigest()

        hash_dir = os.path.join(h[0:1], h[1:2])
        filename = image_guid + '.' + ext

        img_dir = os.path.join(krconfig.work_dir, 'data', 'images', hash_dir)
        fullname = os.path.join(img_dir, filename)
        
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)
        
        localimage = 'images/%s/%s' % (hash_dir, filename)
        return localimage, fullname
   
class ImageDownloader(threading.Thread):
    '''多线程下载图片'''
    global imgq
    def __init__(self, threadname):
        threading.Thread.__init__(self, name = threadname)
        
    def run(self):
        while True:
            i = imgq.get()
            self.getimage(i)
            imgq.task_done()
            
    def getimage(self, i, retires = 1):
        try:
            header = {
                      'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6',
                      'Referer':i['referer']
                    }
            req = urllib2.Request(
                    url = i['url'].encode('utf-8'),
                    headers = header
                    )
            opener = urllib2.build_opener()
            response = opener.open(req, timeout = 30)
            with open(i['filename'], 'wb') as img:
                img.write(response.read())
            if Image and krconfig.grayscale == 1:
                try:
                    img = Image.open(i['filename'])
                    new_img = img.convert("L")
                    new_img.save(i['filename'])
                except:
                    pass
            logging.info("download: {}".format(i['url'].encode('utf-8')))
        except urllib2.HTTPError as http_err:
            if retires > 0:
                return self.getimage(i, retires - 1)
            logging.info("HttpError: {},{}".format(http_err, i['url'].encode('utf-8')))
        except Exception, e:
            if retires > 0:
                return self.getimage(i, retires - 1)
            logging.error("Failed: {}".format(e, i['url'].encode('utf-8')))

class KindleReader(object):
    """core of KindleReader"""
    global imgq
    global feedq
    
    def __init__(self, krconfig):
        pass
      
    def sendmail(self, data):
        """send html to kindle"""
        
        if not krconfig.mail_from:
            raise Exception("'mail from' is empty")
        
        if not krconfig.mail_to:
            raise Exception("'mail to' is empty")
        
        if not krconfig.mail_host:
            raise Exception("'mail host' is empty")
            
        logging.info("send mail to {} ... " .format(krconfig.mail_to))
    
        msg = MIMEMultipart()
        msg['from'] = krconfig.mail_from
        msg['to'] = krconfig.mail_to
        msg['subject'] = 'Convert'
    
        htmlText = 'kindle reader delivery.'
        msg.preamble = htmlText
    
        msgText = MIMEText(htmlText, 'html', 'utf-8')  
        msg.attach(msgText)  
    
        att = MIMEText(data, 'base64', 'utf-8')
        att["Content-Type"] = 'application/octet-stream'
        att["Content-Disposition"] = 'attachment; filename="kindle-reader-%s.mobi"' % (datetime.utcnow() + krconfig.timezone).strftime('%Y%m%d-%H%M%S')
        msg.attach(att)

        try:
            if krconfig.mail_ssl == 1:
                mail = smtplib.SMTP_SSL(timeout = 60)
            else:
                mail = smtplib.SMTP(timeout = 60)

            mail.connect(krconfig.mail_host, krconfig.mail_port)
            mail.ehlo()

            if krconfig.mail_username and krconfig.mail_password:
                mail.login(krconfig.mail_username, krconfig.mail_password)

            mail.sendmail(msg['from'], msg['to'], msg.as_string())
            mail.close()
        except Exception, e:
            logging.error("fail:%s" % e)
        
    def make_mobi(self, user, feeds, format = 'book'):
        """make a mobi file using kindlegen"""
        
        logging.info("generate .mobi file start... ")
        
        data_dir = os.path.join(krconfig.work_dir, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        for tpl in TEMPLATES:
            if tpl is 'book.html':
                continue
                
            t = template.Template(TEMPLATES[tpl])
            content = t.generate(
                user = user,
                feeds = feeds,
                uuid = uuid.uuid1(),
                format = format,
                mobitime = datetime.utcnow() + krconfig.timezone
            )
            
            with open(os.path.join(data_dir, tpl), 'wb') as fp:
                fp.write(content)

        mobi8_file = "KindleReader8-%s.mobi" % (datetime.utcnow() + krconfig.timezone).strftime('%Y%m%d-%H%M%S')
        mobi6_file = "KindleReader-%s.mobi" % (datetime.utcnow() + krconfig.timezone).strftime('%Y%m%d-%H%M%S')
        opf_file = os.path.join(data_dir, "content.opf")
        subprocess.call('%s %s -o "%s" > log.txt' % 
                (krconfig.kindlegen, opf_file, mobi8_file), shell = True)
        
        # kindlegen生成的mobi，含有v6/v8两种格式
        mobi8_file = os.path.join(data_dir, mobi8_file)
        # kindlestrip处理过的mobi，只含v6格式
        mobi6_file = os.path.join(data_dir, mobi6_file)
        if krconfig.kindlestrip == 1:
            # 调用kindlestrip处理mobi
            try:
                data_file = file(mobi8_file, 'rb').read()
                strippedFile = SectionStripper(data_file)
                file(mobi6_file, 'wb').write(strippedFile.getResult())
                mobi_file = mobi6_file
            except Exception, e:
                mobi_file = mobi8_file
                logging.error("Error: %s" % e)
        else:
            mobi_file = mobi8_file
            
        if os.path.isfile(mobi_file) is False:
            logging.error("failed!")
            return None
        else:
            logging.info(".mobi save as: {}({}KB)".format(mobi_file, os.path.getsize(mobi_file) / 1024))
            return mobi_file

    def main(self):
        global updated_feeds     
        feed_idx = 1       
        feed_num = len(krconfig.feeds)
        
        for feed in krconfig.feeds:
            if feed[0:4] == 'full':
                logging.info("[{}/{}](force full text):{}".format(feed_idx, feed_num, feed[4:]))
            else:
                logging.info("[{}/{}]:{}".format(feed_idx, feed_num, feed))
            feedq.put({'feed':feed, 'feed_idx':feed_idx})
            feed_idx += 1
            
        feedthreads = []
        for i in range(krconfig.thread_numbers):
            f = feedDownloader('Threadfeed %s' % (i + 1))
            feedthreads.append(f)
        for f in feedthreads:
            f.setDaemon(True)
            f.start()

        imgthreads = []
        for i in range(krconfig.thread_numbers):
            t = ImageDownloader('Threadimg %s' % (i + 1))
            imgthreads.append(t)
        for t in imgthreads:
            t.setDaemon(True)
            t.start()
            
        feedq.join()
        imgq.join()
        
        if len(updated_feeds) > 0:
            mobi_file = self.make_mobi(krconfig.user, updated_feeds, krconfig.kindle_format)
            if mobi_file and krconfig.mail_enable == 1:
                fp = open(mobi_file, 'rb')
                self.sendmail(fp.read())
                fp.close()
        else:
            logging.info("no feed update.")

if __name__ == '__main__':
    
    logging.basicConfig(level = logging.INFO, format = '%(asctime)s:%(msecs)03d %(levelname)-8s %(message)s',
        datefmt = '%m-%d %H:%M')
    
    try:
        work_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        krconfig = KRConfig(configfile = os.path.join(work_dir, "config.ini"))
    except:
        logging.error("config file {} not found or format error".format(os.path.join(work_dir, "config.ini")))
        sys.exit(1)
        
    if not krconfig.kindlegen:
        logging.error("Can't find kindlegen")
        sys.exit(1)
        
    st = time.time()
    logging.info("welcome, start ...")
        
    try:
        kr = KindleReader(krconfig = krconfig)
        kr.main()
    except Exception, e:
        logging.info("Error: %s " % e)

    logging.info("used time {}s".format(time.time() - st))
    logging.info("done.")
        
    if not krconfig.auto_exit:
        raw_input("Press any key to exit...")
