#!/usr/bin/env python

import os
import json
import gevent
import subprocess
import requests
import requests_cache; requests_cache.install_cache()

MIN_SIZE = (1600, 1200)
RATIO = (1.3, 1.4)

ENDPOINT = 'https://api.flickr.com/services/rest/'

def base_args(apikey):
    return {
        'api_key': apikey,
        'format': 'json',
        'nojsoncallback': 1,
    }

def get_interesting(apikey, workdir):
    args = {
        'method': 'flickr.interestingness.getList',
    }
    args.update(base_args(apikey))
    r = requests.get(ENDPOINT, params=args)
    dat = json.loads(r.text)

    pics = dat['photos']['photo']

    for pic in pics:
        pic_id = pic['id']
        fname = get_pic(apikey, pic_id, workdir)
        if fname:
            return fname


def get_pic(apikey, pic_id, pth, min_size=MIN_SIZE):
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
        if (int(s['width']) > min_size[0]
                and int(s['height']) > min_size[1]):
            ratio = int(s['width']) / float(s['height'])
            if ratio > RATIO[0] and ratio < RATIO[1]:
                src = s['source']
                fname = os.path.join(pth, os.path.basename(src))
                r = requests.get(src)
                with open(fname, 'wb') as f:
                    f.write(r.content)
                print('Wrote file {}'.format(fname))
                return fname
            else:
                print('Wrong ratio of {}'.format(pic_id))
        else:
            print('Wrong size of {}'.format(pic_id))

def set_bg_feh(fname):
    subprocess.check_call(['feh', '--bg-scale', fname])


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description='Download interesting-pictures from flickr')
    parser.add_argument('APIKEY',
                        help='API-key for flickr')
    parser.add_argument('--path',
                        default='/tmp/flickr-downloader',
                        help='Path to download photos to')
    parser.add_argument('--feh',
                        action='store_true',
                        help='Set desktop-background using feh')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()

    os.makedirs(args.path, exist_ok=True)
    fname = get_interesting(apikey= args.APIKEY, workdir=args.path)
    if args.feh:
        set_bg_feh(fname)


