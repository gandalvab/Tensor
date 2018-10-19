# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from bs4 import NavigableString
import os
import json


class TextExtractor:
    def __init__(self, url=None):
        self.__url = url
        self.__text = None
        self.__result = None

    def extract(self, url=None, template=None):
        if url is not None:
            self.__url = url
        if self.__url is None:
            raise ValueError('URL is not set.')

        r = requests.get(self.__url)
        soup = BeautifulSoup(r.text, 'lxml')  #lxml быстрее html.parser  0.073 против 0.118
        self.__text = []
        tagdict = {'h'+str(i): True for i in range(1, 7)}  #TODO: добавить таблицы и div-ы
        tagdict.update({'p': True, 'pre': True, 'li': True, 'span': True})
        donetags = []

        for tag in soup.findAll(tagdict):
            if tag in donetags:
                continue

            if template and template.check(tag):
                continue

            if len(tag.contents) == 1 and isinstance(tag.contents[0], NavigableString):
                self.__text.append((tag.contents[0].string, True))
            else:
                string = [[]]
                TextExtractor.__extract_text(tag, tag.name, donetags, string)
                self.__text.extend([(''.join(i), False) for i in string[0:-1]])
                self.__text.append((''.join(string[-1]), True))

        return len(self.__text)

    def format(self):
        if self.__text is None:
            raise ValueError('Text is not extracted from page. Use extract method before format.')

        self.__result = []
        for line, addblank in self.__text:
            if line.strip():
                self.__result.extend(TextExtractor.__split_string(line, 80))
                if addblank:
                    self.__result.append('')

        return len(self.__result)

    def save(self, fname=None):
        if self.__result is None:
            raise ValueError('Text is not formatted. Use format method before save.')

        if fname is None:
            dirpath, fname, _ = TextExtractor.get_path_params(self.__url)
        else:
            dirpath = os.getcwd()

        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)

        with open(os.path.join(dirpath, fname), 'w', encoding='utf8') as pfile:
            pfile.writelines("%s\n" % item for item in self.__result)
        return len(self.__result)

    @staticmethod
    def get_path_params(url):
        fname = 'index.txt'
        path = url.split('/')
        dirpath = [x for x in path if x not in ['http:', 'https:', '']]
        if path[-1] != '' and path[-1].find('.') > -1:
            dirpath.remove(path[-1])
            fname = path[-1].replace(path[-1][path[-1].find('.') + 1:], 'txt')
        site = dirpath[0]
        dirpath = os.path.join(os.getcwd(), os.sep.join(dirpath).lower())
        return dirpath, fname, site

    @staticmethod
    def __extract_text(tag, tagname, donetags, result):
        for stag in tag:
            if tagname == stag.name:
                result.append([])
            if isinstance(stag, NavigableString):
                result[-1].append(stag.string)
                continue
            if len(stag.contents) == 1 and isinstance(stag.contents[0], NavigableString):
                if stag.name == 'a':
                    if 'href' in stag.attrs:
                        result[-1].extend([stag.string,  ' [', stag.attrs['href'], '] '])
                    else:
                        result[-1].append(stag.string)
                else:
                    if stag.name != 'script':
                        result[-1].append(stag.string)
            else:
                TextExtractor.__extract_text(stag, tagname, donetags, result)
            donetags.append(stag)

    @staticmethod
    def __split_string(val, length):
        ret = list()
        topborder = 0
        botborder = 0
        while topborder < len(val):
            if len(val) - botborder < length:
                topborder = len(val)
            else:
                topborder = val.rfind(' ', botborder + 1, botborder + length)
                if topborder == -1:
                    topborder = botborder + length
            ret.append(val[botborder:topborder].strip())
            botborder = topborder
        return ret


class Template:
    rules = []

    def load(self, file):
        state = True
        try:
            with open(file, 'r') as f:
                self.rules = json.load(f)
        except Exception:
            self.rules = []
            state = False

        self.rules = [Rule(r) for r in self.rules]
        return state

    def check(self, tag):
        return any(rule(tag) for rule in self.rules)


class Rule:
    __obj_dict = {'parent': lambda x: [x.parent], 'parents': lambda x: x.findParents(), 'this': lambda x: [x]}
    __attr_dict = {'class': lambda x: [i.attrs['class'] for i in x if hasattr(i, 'attrs') and 'class' in i.attrs], 'id': lambda x: [i.attrs['id'] for i in x if hasattr(i, 'attrs') and 'id' in i.attrs]}
    __func_dict = {'in': lambda x, y: x in y}

    def __call__(self, *args, **kwargs):
        try:
            obj = self.__obj_dict[self.rule['object']](args[0])
            val = self.__attr_dict[self.rule['attr']](obj)
            return any(self.__func_dict[self.rule['func']](self.rule['val'], i) for i in val)
        except Exception:
            return False

    def __init__(self, rule):
        self.rule = rule
