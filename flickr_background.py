#!/usr/bin/env python

import os
import sys
import json
try:
    import gevent
    from gevent import monkey, pool; monkey.patch_socket(); monkey.patch_ssl()
    has_gevent = 1
except:
    has_gevent=0
import random
import subprocess
import requests
try:
    import requests_cache; requests_cache.install_cache()
except:
    pass

ENDPOINT = 'https://api.flickr.com/services/rest/'

ERROR_NO_DOWNLOAD = -1
ERROR_WRONG_SIZE = -2
ERROR_WRONG_RATIO = -3
ERROR_PARSING = -4

ENV_APIKEY = 'APIKEY_FLICKR'

def log(msg, verbose=True):
    if verbose:
        print(msg)


def post_step(fnames, step_name, verbose):
    """ Call some external program on finished filename """
    STEPS = {
        'feh-bg': ['feh', '--bg-scale', fnames[0]],
    }
    subprocess.check_call(STEPS[step_name])
    log('Post-step: {}'.format(STEPS[step_name]), verbose)


def base_args(apikey):
    return {
        'api_key': apikey,
        'format': 'json',
        'nojsoncallback': 1,
    }


def get_interesting(opts):
    args = {
        'method': 'flickr.interestingness.getList',
    }
    args.update(base_args(opts['apikey']))
    r = requests.get(ENDPOINT, params=args)
    dat = json.loads(r.text)
    if dat['stat'] == 'fail':
        print(dat['message'])
        sys.exit(1)

    pics = dat['photos']['photo']

    if opts['rand']:
        random.shuffle(pics)
    if has_gevent:
        results = get_pics_par(pics, opts)
    else:
        results = get_pics_seq(pics, opts)

    fnames = list(filter(lambda s: isinstance(s, str), results))
    num_dwld = len(fnames)
    num_wrong_ratio = len(list(filter(lambda r: r == ERROR_WRONG_RATIO, results)))
    num_wrong_size = len(list(filter(lambda r: r == ERROR_WRONG_SIZE, results)))
    num_not_allowed=  len(list(filter(lambda r: r == ERROR_NO_DOWNLOAD, results)))

    log('Results', opts['verbose'])
    log('{} interesting flickr-pictures'.format(len(pics)), opts['verbose'])
    log('{} matched filters and were downloaded'.format(num_dwld), opts['verbose'])
    log('{} had wrong ratio'.format(num_wrong_ratio), opts['verbose'])
    log('{} had wrong size'.format(num_wrong_size), opts['verbose'])
    log('{} did not allow downloading'.format(num_not_allowed), opts['verbose'])

    return fnames


def get_pics_seq(pics, opts):
    fnames = []
    for pic in pics:
        pic_id = pic['id']
        fname = get_pic(pic_id, opts=opts)
        fnames.append(fname)
        count = len(list(filter(lambda s: isinstance(s, str), fnames)))
        if opts['count'] and opts['count'] <= count:
            break

    return fnames


def get_pics_par(pics, opts):
    gpool = pool.Pool(10)

    def _get_pic(pic):
        pic_id = pic['id']
        fname = get_pic(pic_id, opts)
        return fname
    fnames = list(gpool.imap(_get_pic, pics))
    return fnames

def get_pic(pic_id, opts):
    fname = None
    try:
        args = {
            'method': 'flickr.photos.getSizes',
            'photo_id': pic_id,
        }
        args.update(base_args(opts['apikey']))
        r = requests.get(ENDPOINT, params=args)
        dat = json.loads(r.text)
        if not bool(int(dat['sizes']['candownload'])):
            if opts['verbose']:
                log('Not allowed to download {}'.format(pic_id), opts['verbose'])
            return ERROR_NO_DOWNLOAD
        wrong_size = True
        for s in dat['sizes']['size']:
            if (int(s['width']) > opts['min_size'][0]
                    and int(s['height']) > opts['min_size'][1]):
                wrong_size = False
                ratio = int(s['width']) / float(s['height'])
                if ratio > opts['ratios'][0] and ratio < opts['ratios'][1]:
                    src = s['source']
                    fname = os.path.join(opts['workdir'], os.path.basename(src))
                    r = requests.get(src)
                    with open(fname, 'wb') as f:
                        f.write(r.content)
                    if opts['verbose']:
                        log('Wrote file {}'.format(fname), opts['verbose'])
                    return fname
                else:
                    log('Wrong ratio of {}'.format(pic_id), opts['verbose'])
                    return ERROR_WRONG_RATIO
        if wrong_size:
            log('Wrong size of {}'.format(pic_id), opts['verbose'])
            return ERROR_WRONG_SIZE
    except:
        fname = ERROR_PARSING
        log("ERROR while parsing {}".format(pic_id), opts['verbose'])
    return fname


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description=("Download interesting-pictures from flickr. "
                     "Reads flickr-apikey from env-var {} "
                     "or optional --apikey-flag.".format(ENV_APIKEY)))
    parser.add_argument('-k', '--apikey',
                        help='API-key for flickr')
    parser.add_argument('-p', '--path',
                        default='/tmp/flickr-downloader',
                        help='Path to download photos to')
    parser.add_argument('-c', '--count',
                        default=5,
                        help='Download this many pictures.')
    parser.add_argument('-r', '--random',
                        default=False,
                        action='store_true',
                        help='Randomly pick interesting photos')
    parser.add_argument('-m', '--min-size',
                        default='1600x1200',
                        help='Minimum dimensions of sought photos. '
                             'Example: "1600x1200".')
    parser.add_argument('-q', '--ratios',
                        default='1.3-1.4',
                        help='Look for picture-ratios in this range.')
    parser.add_argument('-t', '--threads',
                        default=10,
                        help='Number of green threads used for downloading.')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Verbose output')
    parser.add_argument('-e', '--post-step',
                        choices=('feh-bg',),
                        help='feh-bg : Set desktop-background using feh.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    apikey = args.apikey or os.getenv(ENV_APIKEY)
    if not apikey:
        print('ERROR: No apikey found. Supply one in {}-env-var or as --api-key APIKEY'
              .format(ENV_APIKEY))
        sys.exit(1)
    os.makedirs(args.path, exist_ok=True)
    opts = {
        'apikey': apikey,
        'workdir': args.path,
        'count': args.count,
        'rand': args.random,
        'min_size': tuple(map(int, args.min_size.split('x'))),
        'ratios': tuple(map(float, args.ratios.split('-'))),
        'verbose': args.verbose,
    }
    fnames = get_interesting(opts=opts)
    if not fnames:
        print("No pictures downloaded")
        sys.exit(1)

    if args.post_step:
        post_step(fnames, args.post_step, args.verbose)


