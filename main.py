# -*- coding: utf-8 -*-
import os
import sys
from TextExtractor import TextExtractor, Template

if len(sys.argv) < 2:
    print('No URL')
    exit(1)

url = sys.argv[1]

try:
    _, _, site = TextExtractor.get_path_params(url)
    template = Template()
    file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', site)
    print('Loading template from file', file)
    if not template.load(file):
        print('Template not loaded')

    extractor = TextExtractor()
    extractor.extract(url, template)
    count = extractor.format()
    extractor.save()
except Exception as err:
    print('Error', err.args)
else:
    print(count, 'line(s) saved to file ', os.sep.join(TextExtractor.get_path_params(url)[0:2]))
