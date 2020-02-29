#! python
# charset=utf-8

# create a new post with a proper and correct formated title.

import datetime
import sys

config = '''---
layout: post
title:  #title
date:   #time
author: dox4
categories: TODO
---
'''

def today():
    today = datetime.datetime.now()
    return today.strftime("%Y-%m-%d %H:%M:%S")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('please input a title for your new post:')
        title = input()
    else:
        title = sys.argv[1]
    t = today()
    with open('_posts/' + t.split(' ')[0] + '-' + title.replace(' ', '-') + '.markdown', 'w', encoding='utf-8') as md:
        md.write(config.replace('#title', title).replace('#time', t + ' +0800'))