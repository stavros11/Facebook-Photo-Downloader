"""Classes for Facebook scraping."""
import os
import shutil
import time
import requests
import bs4

import profiles
from typing import Optional


class FacebookSession:

  def __init__(self, session: Optional[requests.session] = None,
               base_url="https://m.facebook.com"):
    self.base_url = base_url
    if session is None:
      self.session = requests.session()
    else:
      self.session = session

  def login(self, email: str, password: str):
    self.session.headers.update(
        {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:39.0) Gecko/20100101 Firefox/39.0'})

    # Navigate to Facebook's homepage to load Facebook's cookies.
    response = self.session.get(self.base_url)
    # Attempt to login to Facebook
    response = self.session.post('{}/login.php'.format(self.base_url),
                                 data={'email': email, 'pass': password},
                                 allow_redirects=False)

  def _get(self, url, **kwargs):
    attempts = kwargs.pop("attempts") if "attempts" in kwargs else 5
    retry_time = kwargs.pop("retry_time") if "retry_time" in kwargs else 5

    page = self.session.get(url, **kwargs)
    while page.status_code != 200 and attempts > 0:
      attempts -= 1
      print("WARNING: Url {} opened with invalid status code {}. {} attempts "
            "remaining.".format(url, page.status_code, attempts))
      time.sleep(retry_time)
      page = self.session.get(url, **kwargs)

    if page.status_code != 200:
      raise ValueError("Connection failed with.")

    return page

  def get(self, link, attempts: int = 5, retry_time: int = 5):
    url = "/".join([self.base_url, link])
    return self._get(url, attempts=attempts, retry_time=retry_time)

  def get_large_photo(self, url, attempts: int = 5, retry_time: int = 5):
    return self._get(url, attempts=attempts, retry_time=retry_time,
                     stream=True)


class ScrapableFacebookProfile(profiles.FacebookProfile):

  def scrape(self, session: FacebookSession, sleep_time: int = 1):
    # Get profile page
    profile_page = session.get(self.id)
    profile_soup = bs4.BeautifulSoup(profile_page.text, "html.parser")
    del profile_page
    # Set names from profile page
    self.set_name(profile_soup)
    # Find profile and cover photo urls
    self.set_photo_urls(profile_soup)

    time.sleep(sleep_time)
    # Get about page
    about_page = session.get("/".join([self.id, "about"]))
    about_soup = bs4.BeautifulSoup(about_page.text, "html.parser")
    del about_page
    # Set places from about page
    self.set_about(about_soup)


  def download_next_photo(self, session: FacebookSession, sleep_time: int = 1):
    if self.local_photo_dir is None:
      raise ValueError("Cannot download photos for {} because a local "
                       "directory is not set.".format(self.id))

    if self.photos:
      # Downloading the photo that is right after the last downloaded photo
      if not self.photos[-1].is_downloaded:
        print("WARNING: Photo {} of {} is not downloaded locally in {}.".format(
            self.photos[-1].id, self.id, self.local_photo_dir))
      photo_url = self.photos[-1].next_url
    else:
      # Downloading the first photo starting with the profile url
      if self.profile_photo_url is None:
        raise ValueError("Cannot download photos for {} because a photo url "
                         "is not available and there are no available "
                         "photos.".format(self.id))
      photo_url = self.profile_photo_url
    if photo_url is None:
      print("WARNING: Could not find next photo for {}. We already have {} "
            "photos for this profile.".format(self.id, len(self.photos)))
    else:
      new_photo = ScrapableFacebookPhoto(photo_url, local_dir=self.local_photo_dir)
      new_photo.download(session, sleep_time)
      self.photos.append(new_photo)

  def set_name(self, soup: bs4.BeautifulSoup):
    """Scrapes name from profile page <title>."""
    titles = soup.find_all("title")
    if len(titles) > 1:
      print("WARNING: Multiple titles found in the name page of {}. "
            "Only the first title is used.".format(self.id))
    all_names = titles[0].get_text().split(" ")

    self._first_name = " ".join(all_names[:-1])
    self._last_name = all_names[-1]

  def set_photo_urls(self, soup: bs4.BeautifulSoup):
    """Finds the profile and cover photo urls from the profile main page."""
    all_href = soup.find_all("a", href=True)
    photo_href = [x for x in all_href if "photo" in x["href"]]
    if len(photo_href) < 2:
      raise ValueError("Found {} photo hrefs for {}.".format(
          len(photo_href), self.id))
    # Assume the first photo url is the cover photo and the second the profile
    self.cover_photo_url = photo_href[0]["href"].replace("amp;", "")
    self.profile_photo_url = photo_href[1]["href"].replace("amp;", "")

  _ABOUT_TARGETS = {"Education", "Places He's Lived", "Contact Info"}

  def set_about(self, soup: bs4.BeautifulSoup):
    """Scrapes place of birth and residence from about page."""
    # Find about section class attribute (eg. "do", "dm", ...)
    class_attrs = {}
    for span in soup.find_all("span", {"class": True}):
      if span.text in self._ABOUT_TARGETS:
        class_attrs[span.text] = span.attrs["class"][0]
    if len(class_attrs) < 1:
      print("WARNING: Failed to find about section class attributes for {}."
            "".format(self.id))
    else:
      if len(set(class_attrs.values())) > 1:
        print("WARNING: Different about section class attributes were "
              "identified for {}. Using `Places` attribute.".format(self.id))
      if "Places He's Lived" in class_attrs:
        attrs = class_attrs["Places He's Lived"]
      else:
        print("WARNING: Failed to find `Places` class attribute for {}. Using "
              "different attribute to scrape about section.".format(self.id))
        attrs = set(class_attrs.values()).pop()

      data = soup.find_all("span", attrs)
      self.about_dict = {x.text: x.find_next().text for x in data}
      if "Hometown" in self.about_dict:
        self.hometown = self.about_dict["Hometown"]
      if "Current City" in self.about_dict:
        self.current_city = self.about_dict["Current City"]


class ScrapableFacebookPhoto(profiles.FacebookPhoto):

  def download(self, session: FacebookSession, sleep_time: int = 1):
    if self.local_dir is None:
      raise ValueError("Cannot download photo {} because a local "
                       "directory was not provided.".format(self.id))

    if self.is_downloaded:
      raise NameError("A photo with id {} already exists in {}.".format(
          self.id, self.local_dir))

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
    photo_filename = os.path.join(self.local_dir, self.filename)
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
