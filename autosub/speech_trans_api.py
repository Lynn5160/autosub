#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines speech and translation api used by autosub.
"""

from __future__ import absolute_import, unicode_literals

# Import built-in modules
import json
try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

# Import third-party modules
import requests
from googleapiclient.discovery import build

# Any changes to the path and your own modules


class GoogleSpeechToTextV2(object):  # pylint: disable=too-few-public-methods
    """
    Class for performing speech-to-text for an input FLAC file.
    """
    def __init__(self,
                 api_url,
                 api_key,
                 min_confidence=0.0,
                 lang_code="en",
                 rate=44100,
                 retries=3):
        # pylint: disable=too-many-arguments
        self.min_confidence = min_confidence
        self.lang_code = lang_code
        self.rate = rate
        self.api_url = api_url
        self.api_key = api_key
        self.retries = retries

    def __call__(self, data):
        try:  # pylint: disable=too-many-nested-blocks
            for _ in range(self.retries):
                url = self.api_url.format(lang=self.lang_code, key=self.api_key)
                headers = {"Content-Type": "audio/x-flac; rate=%d" % self.rate}

                try:
                    result = requests.post(url, data=data, headers=headers)
                except requests.exceptions.ConnectionError:
                    continue

                for line in result.content.decode('utf-8').split("\n"):
                    try:
                        line = json.loads(line)
                        line_dict = line
                        if 'result' in line and line['result'] \
                                and 'alternative' in line['result'][0] \
                                and line['result'][0]['alternative'] \
                                and 'transcript' in line['result'][0]['alternative'][0]:
                            line = line['result'][0]['alternative'][0]['transcript']

                            if 'confidence' in line_dict['result'][0]['alternative'][0]:
                                confidence = \
                                    float(line_dict['result'][0]['alternative'][0]['confidence'])
                                if confidence > self.min_confidence:
                                    result = line[:1].upper() + line[1:]
                                    result = result.replace('’', '\'')
                                    return result
                                return ""

                            else:
                                # can't find confidence in json
                                # means it's 100% confident
                                result = line[:1].upper() + line[1:]
                                result = result.replace('’', '\'')
                                return result
                        else:
                            continue

                    except (JSONDecodeError, ValueError, IndexError):
                        # no result
                        continue

        except KeyboardInterrupt:
            return None

        return ""


class GoogleTranslatorV2(object):  # pylint: disable=too-few-public-methods
    """
    Class for GoogleTranslatorV2 translating text from one language to another.
    """
    def __init__(self, api_key, src, dst):
        self.api_key = api_key
        self.service = build('translate', 'v2',
                             developerKey=self.api_key)
        self.src = src
        self.dst = dst

    def __call__(self, trans_list):
        try:
            if not trans_list:
                return None

            trans_str = '\n'.join(trans_list)

            result = self.service.translations().list(  # pylint: disable=no-member
                source=self.src,
                target=self.dst,
                q=[trans_str]
            ).execute()

            if 'translations' in result and result['translations'] and \
                    'translatedText' in result['translations'][0]:
                return '\n'.split(result['translations'][0]['translatedText'])

            return None

        except KeyboardInterrupt:
            return None