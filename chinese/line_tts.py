# -*- mode: python; coding: utf-8 -*-
#
# Copyright © 2012 Roland Sieker, ospalh@gmail.com
# Inspiration and source of the URL: Tymon Warecki
# Adapted by Thomas TEMPE, thomas.tempe@alysse.org
#
# License: GNU AGPL, version 3 or later; http://www.gnu.org/copyleft/agpl.html


'''
Download Chinese pronunciations from LINE dictionary
'''

import json
import urllib
import urllib2
import os
import re
import time

from aqt import mw


download_file_extension = u'.mp3'
autocomplete_url = "http://ce.linedict.com/ac?dictType=cnen&st=100&&_t={time}&q={query}"
dict_url = "http://linedict.naver.com/267/cnen/entry/json/{hash}?defaultPron=US&hash=true&_={time}"
pronunciation_url = "http://ce.linedict.com/dictPronunciation.dict?filePaths={path}"
user_agent_string = 'Mozilla/5.0'


def get_word_from_line(source, lang = 'zh'):
    filename, fullpath = get_filename("_".join([source, "G", lang]), download_file_extension)
    if os.path.exists(fullpath):
        return filename

    # Autocomplete API call.
    query_str = urllib.quote(source.encode("utf-8"))
    ac_r = make_request(autocomplete_url, time=int(time.time()),
                        query=query_str)
    ac_json = json.loads(ac_r.read())
    ac_r.close()
    # Parse AC results.
    # Exceptions caught by caller.
    ac_item = ac_json["items"][0][0]
    if ac_item[2][0] != source:
        print(ac_item[2][0])
        raise ValueError(u"First result %u != source %u"
                         % (ac_item[2][0], source))
    item_hash = ac_item[1][0]

    # Dictionary API call.
    dict_r = make_request(dict_url, hash=item_hash, time=int(time.time()))
    dict_json = json.loads(dict_r.read())
    dict_r.close()
    # Parse dictionary results.
    prons = dict_json["prons"]["de"]
    try:
        pron_path = prons["pronFileM_vcode"]
    except KeyError:
        pron_path = prons["pronFileF_vcode"]

    # Pronunciation API call.
    pron_r = make_request(pronunciation_url, path=urllib.quote(pron_path))
    pron_json = json.loads(pron_r.read())
    pron_r.close()
    # Parse pronunciation results.
    audio_url = pron_json["url"][0]

    # FINALLY, download the audio.
    audio_r = make_request(audio_url)
    with open(fullpath, "wb") as audio_file:
        audio_file.write(audio_r.read())
    audio_r.close()

    return filename


def make_request(url_template, timeout=5, **kwargs):
    url = url_template.format(**kwargs)
    request = urllib2.Request(url)
    request.add_header("User-agent", user_agent_string)
    response = urllib2.urlopen(request, timeout=timeout)
    if 200 != response.code:
        raise ValueError(str(response.code) + ": " + response.msg)
    return response


def get_filename(base, end):
    """Return the media filename for the given title. """
    # Basically stripping the 'invalidFilenameChars'. (Not tested too much).
    base = re.sub('[\\/:\*?"<>\|]', '', base)
    mdir = mw.col.media.dir()
    return base + end, os.path.join(mdir, base + end)
