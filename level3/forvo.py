#!/usr/bin/env python3
import re
import traceback

import requests
import json
import base64
from random import randint
from time import sleep
from pydub import AudioSegment
import os
import urllib.parse

from loguru import logger


class ForvoUtil:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
        self.language = ""

    def _get_mp3_url(self, word):
        if word is None or len(word) == 0:
            logger.info("word {} is empty string or None, wont be processed. ".format(word))
            return []
        word = urllib.parse.quote_plus(word)
        # web_page_url = "https://forvo.com/word/{}/#{}".format(word, self.language)
        if self.language is not None and len(self.language) > 0:
            web_page_url = "https://forvo.com/search/{}/{}/".format(word, self.language)
        else:
            web_page_url = "https://forvo.com/search/{}/".format(word, self.language)
        logger.info("word {}, request url {}".format(word, web_page_url))
        web_page_text = requests.get(web_page_url, headers=self.headers, timeout=10).text
        # print(web_page_text)
        paths = re.findall("Play\(\d+,'(.*?)'", web_page_text)
        logger.info("mp3 paths: {}".format(paths))
        paths = ['https://audio00.forvo.com/mp3/{}'.format(base64.b64decode(path).decode()) for path in paths]
        return paths

    def fetch_raw_mp3(self, word, base_path="") -> bool:
        paths = self._get_mp3_url(word)
        if len(paths) == 0:
            logger.info("word {}, url empty, no mp3 file will be downloaded.".format(word))
            return False
        try:
            logger.info("word {}, fetch mp3 files.".format(word))
            response = requests.get(paths[0], headers=self.headers)
            if base_path:
                os.makedirs(base_path, exist_ok=True)
            file_name = self.get_audio_file_name(word)
            file_name = os.path.join(base_path, file_name)
            with open(file_name, "wb") as f:
                f.write(response.content)
            logger.info("word {}, done".format(word))
        except Exception as e:
            logger.error("download exception {}".format(e))
            return False
        # "ffplay -autoexit -nodisp sangiovese.mp3"
        return True

    def get_audio_file_name(self, word):
        return "{}.mp3".format(word)

    def fetch_from_file(self, file_name, save_dir, force_fetch=False):
        with open(file_name) as file:
            lines = [line.strip() for line in file]
        logger.info("ready to fetch audios from a list of {} words, with an interval of 1~5 seconds".format(len(lines)))
        for word in lines:
            if self.audio_file_exists(save_dir, word) and not force_fetch:
                logger.info("audio file already exists for word {}, skip download".format(word))
                continue
            self.fetch_raw_mp3(word, save_dir)
            sleep(randint(1, 5))

    def get_word_file_map(self, file_names, base_dir, suffix=".mp3"):
        word_file_map = {}
        for file_name in file_names:
            word = file_name.replace(base_dir,"").replace(suffix, "").replace("/","")
            word_file_map[word] = file_name
        return word_file_map

    def get_file_names(self, base_path):
        file_names = []
        for fn in os.listdir(base_path):
            f = os.path.join(base_path, fn)
            if os.path.isfile(f):
                file_names.append(f)
        return file_names


    def sort_file_names(self, word_file_map, order_file):
        result = []
        with open(order_file) as file:
            lines = [line.strip() for line in file]
        for line in lines:
            if line in word_file_map.keys():
                result.append(word_file_map[line])
        return result

    def _merge_audio_files(self, file_names, merge_file_name, silence=0):
        audio = None
        contents = []
        gap = AudioSegment.silent(duration=silence * 1000)
        for file_name in file_names:
            logger.info("merging {}".format(file_name))
            temp_audio = AudioSegment.from_mp3(file_name)
            temp_audio = temp_audio + temp_audio
            audio = temp_audio if audio is None else audio + temp_audio
        audio = audio + AudioSegment.silent(2000)
        logger.info("saving mp3 file")
        audio.export(merge_file_name, format="mp3")
        logger.info("done")

    def audio_file_exists(self, audio_file_path, word):
        fn = self.get_audio_file_name(word)
        f = os.path.join(audio_file_path, fn)
        return os.path.isfile(f)

    def merge_audio_files(self, merge_file_name, audio_file_path, order_file=None):
        logger.info("merging files in {} into audio file {}, by the order of file {}".format(audio_file_path, merge_file_name, order_file))
        file_names = self.get_file_names(audio_file_path)
        print(file_names)
        word_file_map = self.get_word_file_map(file_names, audio_file_path)
        if order_file:
            try:
                file_names = self.sort_file_names(word_file_map, order_file)
            except Exception as e:
                logger.error("exception occurred in sorting file names, {}".format(traceback.format_exc()))
            print(file_names)
        self._merge_audio_files(file_names, merge_file_name)
        logger.info("merge completed.")



if __name__ == '__main__':
    forvo = ForvoUtil()

    # forvo.fetch_raw_mp3("Saint-Estèphe", base_path)
    # forvo.fetch_from_file("france_region.txt")

    # forvo.get_file_names(base_path)
    #
    # base_path = "france_region"
    # forvo.language="fr"

    # base_path = "italy_region"

    # base_path = "germany_austria_region"
    # forvo.language = "de"
    #
    # base_path = "spain_portugal_region"
    # forvo.language = "es"
    # forvo.language = "ca"
    # forvo.language = "pt"

    base_file_name = "spain_portugal_other"
    audio_file_path = "other_terms"
    # forvo.language = "fr"
    # forvo.language = "de"
    # forvo.language = "it"
    # forvo.language = "pt"



    words_file_name = "{}.txt".format(base_file_name)
    merge_file_name = "{}.mp3".format(base_file_name)

    forvo.fetch_from_file(words_file_name, audio_file_path)
    forvo.merge_audio_files(merge_file_name, audio_file_path, words_file_name)

