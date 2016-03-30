

Flickr-downloader
===================


Simple script for dowloading latest interesting pictures from flickr.

Optionally set as background using feh.

Example
-------

    ./flickr_background.py --rand --verbose \
        --min-size 1280x720 --ratios 1.7-1.8 --post-step feh-bg

Usage
------
```
usage: flickr_background.py [-h] [-k APIKEY] [-p PATH] [-c COUNT] [-r]
                            [-m MIN_SIZE] [-q RATIOS] [-t THREADS] [-v]
                            [-e {feh-bg}]

Download interesting-pictures from flickr. Reads flickr-apikey from env-var
APIKEY_FLICKR or optional --apikey-flag.

optional arguments:
  -h, --help            show this help message and exit
  -k APIKEY, --apikey APIKEY
                        API-key for flickr
  -p PATH, --path PATH  Path to download photos to
  -c COUNT, --count COUNT
                        Download this many pictures.
  -r, --random          Randomly pick interesting photos
  -m MIN_SIZE, --min-size MIN_SIZE
                        Minimum dimensions of sought photos. Example:
                        "1600x1200".
  -q RATIOS, --ratios RATIOS
                        Look for picture-ratios in this range.
  -t THREADS, --threads THREADS
                        Number of green threads used for downloading.
  -v, --verbose         Verbose output
  -e {feh-bg}, --post-step {feh-bg}
                        feh-bg : Set desktop-background using feh.
```
Dependencies
-------------

 * Python3
 * requests
 * requests-cache (optional, minimizes web-traffic in subsequent runs)
 * gevent (optional, speeds up fetching)

