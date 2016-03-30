#!/usr/bin/env python

import os
import sys
import json
import gevent
import random
import subprocess
import requests
import requests_cache; requests_cache.install_cache()

ENDPOINT = 'https://api.flickr.com/services/rest/'


def post_step(fname, step_name):
    """ Call some external program on finished filename """
    STEPS = {
        'feh-bg': ['feh', '--bg-scale', fname],
    }
    subprocess.check_call(STEPS[step_name])


def base_args(apikey):
    return {
        'api_key': apikey,
        'format': 'json',
        'nojsoncallback': 1,
    }


def get_interesting(apikey, opts):
    args = {
        'method': 'flickr.interestingness.getList',
    }
    args.update(base_args(apikey))
    r = requests.get(ENDPOINT, params=args)
    dat = json.loads(r.text)

    pics = dat['photos']['photo']

    if opts['rand']:
        random.shuffle(pics)
    for pic in pics:
        pic_id = pic['id']
        fname = get_pic(apikey, pic_id, opts=opts)
        if fname:
            return fname


def get_pic(apikey, pic_id, opts):
    args = {
        'method': 'flickr.photos.getSizes',
        'photo_id': pic_id,
    }
    args.update(base_args(apikey))
    r = requests.get(ENDPOINT, params=args)
    dat = json.loads(r.text)
    if not bool(int(dat['sizes']['candownload'])):
        print('Not allowed to download {}'.format(pic_id))
        return
    for s in dat['sizes']['size']:
        if (int(s['width']) > opts['min_size'][0]
                and int(s['height']) > opts['min_size'][1]):
            ratio = int(s['width']) / float(s['height'])
            if ratio > opts['ratios'][0] and ratio < opts['ratios'][1]:
                src = s['source']
                fname = os.path.join(opts['workdir'], os.path.basename(src))
                r = requests.get(src)
                with open(fname, 'wb') as f:
                    f.write(r.content)
                print('Wrote file {}'.format(fname))
                return fname
            else:
                print('Wrong ratio of {}'.format(pic_id))
        else:
            print('Wrong size of {}'.format(pic_id))


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description=("Download interesting-pictures from flickr. "
                     "Reads flickr-apikey from env-var APIKEY_FLICKR "
                     "or optional --apikey-flag."""))
    parser.add_argument('--apikey',
                        help='API-key for flickr')
    parser.add_argument('--path',
                        default='/tmp/flickr-downloader',
                        help='Path to download photos to')
    parser.add_argument('-r', '--random',
                        default=False,
                        action='store_true',
                        help='Randomly pick interesting photo')
    parser.add_argument('--min-size',
                        default='1600x1200',
                        help='Minimum dimensions of sought photos. '
                             'Example: "1600x1200".')
    parser.add_argument('--ratios',
                        default='1.3-1.4',
                        help='Look for picture-ratios in this range. '
                             'Example: "1.3-1.4".')
    parser.add_argument('--post-step',
                        choices=('feh-bg',),
                        help='feh-bg : Set desktop-background using feh.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    apikey = args.apikey or os.getenv('APIKEY_FLICKR')
    if not apikey:
        print('ERROR: No apikey found')
        sys.exit(1)
    os.makedirs(args.path, exist_ok=True)
    opts = {
        'workdir': args.path,
        'rand': args.random,
        'min_size': tuple(map(int, args.min_size.split('x'))),
        'ratios': tuple(map(float, args.ratios.split('-'))),
    }
    fname = get_interesting(apikey=apikey,
                            opts=opts)
    if args.post_step:
        post_step(fname, args.post_step)


