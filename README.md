# Facebook-Photo-Downloader
This is a simple bot/scraper for downloading profile photos from facebook. It only requires your facebook email and password (for logging in) and a list of facebook profile IDs (not necessary of friends) and it will download their profile photos on your local disk in the highest available resolution.

Note that there are various (functioning and no) Facebook scrapers on GitHub. This project has limited capabilities and does not intend to compete with them. It was mainly developed as a fun way of learning scraping methods. Because of its simple use, I hope it may be useful to other people as well.

## Disclaimer
Using automated bots on Facebook is **against** its terms of use. Using this code extensively (on more than ~40 profiles in one sitting) may **block** some features of your Facebook account for a short period of time. 
I developed the code purely for educational purposes and I do not intend to use extensively. I do not bare any responsibility for any misuse by other users.


## Usage

#### Dependencies
Make sure that you have the following dependencies installed: `bs4`, `pandas`, `requests`.

The code was tested to work on a clean `virtualenv` environment with `Python 3.6` on `Ubuntu 18.04`. 
Note that I have not implemented any unit testing and therefore bugs are very likely!

#### How-to
First create a file that contains a list of Facebook IDs for the people you would like to download photos. 

The file can be :

1. A pickle (`.pkl`) that contains a Python list with the IDs as strings.
2. A text file (`.txt`) that contains a single ID in each line.

*NOTE:* Facebook ID is the name contained in the profile page URL. Navigating to `www.facebook.com/'facebook-id'` (without `'`) should give you the main profile page of the corresponding person.

*NOTE 2:* In the future I may add a script that generates the file with Facebook IDs automatically from the list of your friends or the friends of a friend.

Then use the following bash template:
```bash
FILE=(full path for your file with the IDs to scrape)
EMAIL=(your facebook email)
PASS=(your facebook password)

python3 main.py --friends-file $FILE --max-photos 3 --email $EMAIL --password $PASS
```

Note that you need your facebook credentials to log-in, in order to access the high resolution photos of your friends (and sometimes even people who are not your friends).


