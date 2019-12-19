"""Data structures for facebook photos."""
import os
import time
import shutil
import bs4
from downloader import facebook
from typing import Optional, Tuple


class FacebookPhoto:
  """Base photo data structure."""

  def __init__(self,
               main_page_url: str,
               folder_path: str,
               large_photo_url: Optional[str] = None):
    self.id = self.find_photo_id(main_page_url)
    self.folder_path = folder_path

    self.main_page_url = main_page_url
    self.large_photo_url = large_photo_url

    self._previous = None
    self._next = None

    self.facebook_page_url = None
    self.facebook_large_photo_url = None

  @property
  def previous_url(self) -> str:
    """URL of the previous photo in the photo reel."""
    return self._previous

  @property
  def next_url(self) -> str:
    """URL of the next photo in the photo reel."""
    return self._next

  @property
  def neighbor_urls(self) -> Tuple[str, str]:
    """Tuple of previous and next URLs."""
    return (self._previous, self._next)

  @property
  def filename(self) -> str:
    """Creates the local file name for the photo."""
    return ".".join([self.id, "jpg"])

  @property
  def is_downloaded(self) -> bool:
    """True if the photo is downloaded locally, else False."""
    return self.filename in set(os.listdir(self.folder_path))

  def describe(self):
    print("Photo page url:")
    print(self.facebook_page_url)
    print("\nLarge photo url:")
    print(self.facebook_large_photo_url)

  @staticmethod
  def find_photo_id(url: str) -> str:
    """Finds the facebook photo ID given the photo page url."""
    url_without_options = url.split("&")[0]
    fbid = url_without_options.split("?")[-1]
    key, value = fbid.split("=")
    assert key == "fbid"
    return value


class ScrapableFacebookPhoto(FacebookPhoto):
  """Photo data structure for scraping and downloading."""

  def download(self, session: facebook.FacebookSession, sleep_time: int = 1):
    """Downloads the large version of the photo locally on disk."""
    if self.is_downloaded:
      raise NameError("A photo with id {} already exists in {}.".format(
          self.id, self.folder_path))

    # Get photo main page
    main_page = session.get(self.main_page_url)
    main_soup = bs4.BeautifulSoup(main_page.text, "html.parser")
    del main_page
    # Set next and previous photos and find redirect page url
    self.set_previous_and_next_photos(main_soup)
    redirect_url = self.find_view_full_size_redirect_url(main_soup)

    # Get redirect page and find large image url
    time.sleep(sleep_time)
    redirect_page = session.get(redirect_url)
    redirect_soup = bs4.BeautifulSoup(redirect_page.text, "html.parser")
    del redirect_page
    self.set_large_photo_url(redirect_soup)

    # Download large photo
    photo_filename = os.path.join(self.folder_path, self.filename)
    photo_page = session.get_large_photo(self.large_photo_url)
    with open(photo_filename, "wb") as photo_file:
      shutil.copyfileobj(photo_page.raw, photo_file)
    del photo_page

  def find_view_full_size_redirect_url(self, soup: bs4.BeautifulSoup) -> str:
    """Finds the large photo redirect url from the profile photo page."""
    urls = [x["href"] for x in soup.find_all("a", href=True)
            if "view_full_size" in x["href"]]
    if len(urls) > 1:
      print("WARNING: Found more than one `view_full_size` urls for "
            "{}.".format(self.id))

    return str(urls[0]).replace("amp;", "")

  def set_previous_and_next_photos(self, soup: bs4.BeautifulSoup):
    """Sets the URLs of previous and next photos on the reel."""
    hrefs = soup.find_all("a", href=True)
    photo_hrefs = [x["href"] for x in hrefs if "/photo" in x["href"]]
    if len(photo_hrefs) < 2:
      print("WARNING: Found only {} photo links while searching for previous "
            "and next photos of {}.".format(len(photo_hrefs), self.id))
      if len(photo_hrefs) == 1:
        self._next = photo_hrefs[0]
    else:
      self._previous = photo_hrefs[0]
      self._next = photo_hrefs[1]

  def set_large_photo_url(self, soup: bs4.BeautifulSoup):
    """Finds actual large photo link from the redirect page."""
    meta = soup.find_all("meta")
    assert len(meta) == 1
    meta = str(meta[0])

    ind = meta.find("url")
    url = meta[ind + 4:]
    url = url.split(" ")
    assert len(url) == 2
    self.large_photo_url = url[0][:-1].replace("amp;", "")
