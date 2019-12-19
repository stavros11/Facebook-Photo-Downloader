# Facebook-Photo-Downloader
This is a simple scraper for downloading profile photos from facebook. It only requires your facebook email and password (for logging in) and a list of facebook profile IDs (not necessary of friends) and it will download their profile photos on your local disk in the highest available resolution.

Note that there are various Facebook scrapers on GitHub. This project has limited capabilities and does not intend to compete with them. It was developed as a fun way of learning scraping methods. Because of its simple use, it may be useful to other people as well.

## Disclaimer
Using automated bots on Facebook is **against** its terms of use. Using this code extensively (on more than ~40 profiles in one sitting) may **block** some features of your Facebook account for a short period of time. 
I developed the code purely for educational purposes and I do not intend to use extensively. I do not bare any responsibility for any misuse by others.


## Usage

#### Dependencies
Make sure that you have the following dependencies installed: `bs4`, `pandas`, `requests`.

The code was tested to work on a clean `virtualenv` environment with `Python 3.6` on `Ubuntu 18.04`. 
Nevertheless, note that there is no unit testing implemented and therefore bugs are very likely!

#### Quick How-To
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

python3 main.py --friends-file $FILE --email $EMAIL --password $PASS --max-photos 3 
```

Note that you need to log in for accessing the high resolution photos of your friends (and sometimes also people who are not your friends). This is why your facebook credentials are required to run.

Max photos sets the number of photos you would like to download from each person in the list. If the person has less available profile photos then all his photos will be downloaded.

Running the above will download the photos of the specified people in the directory of `FILE`. A different folder with the photos will be created for each person. A `pd.DataFrame` will also be saved as `profiles.pkl` and will contain various scraped data for the profiles, such the names, cities, about sections and photo urls.

#### Optional options
You can also set the following flags:
* `--data-dir` : Alternative path to save downloaded photos. If set, this will be used instead of the `FILE` directory.
* `--sleep-time`: Time to wait between subsequent HTTP requests when scraping a single profile (defaults to 1 sec).
* `--sleep-between`: Time to wait between subsequent HTTP requests when scraping a single profile (defaults to 3 sec).
* `--start` and `--end` can be used to index the loaded friend list from `FILE` if we don't want to scrape all people it contains (for example when resuming an old scraping session).

It is common to use `sleep` when sending HTTP requests to avoid overloading the server. Note that even if you use larger `sleep` times, your facebook profile will get blocked after scraping many profiles. Nevertheless, be polite and :sleeping: sufficiently long! :wink:


## Acknowledgement

The code uses the mobile version of the Facebook website as this was the only one that I managed to make logging in to work. I used the [gist](https://gist.github.com/UndergroundLabs/fad38205068ffb904685) by [UndergroundLabs](https://gist.github.com/UndergroundLabs) for this.
