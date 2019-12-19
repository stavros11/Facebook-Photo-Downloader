"""Basic data structures for profiles and photos."""
import inspect
import time
import os
import bs4
from downloader import facebook
from downloader import photos
from typing import Any, Dict, Optional


class FacebookProfile:
  """Base profile data structure."""

  def __init__(self,
               id: str,
               database_path: str,
               first_name: Optional[str] = None,
               last_name: Optional[str] = None,
               hometown: Optional[str] = None,
               current_city: Optional[str] = None,
               profile_photo_url: Optional[str] = None,
               cover_photo_url: Optional[str] = None):
    # Required information
    self.id = id
    self.database_path = database_path

    # Facebook name
    self._first_name = first_name
    self._last_name = last_name

    # Information found in about page
    self.hometown = hometown
    self.current_city = current_city
    self.about_dict = {}
    # Photos
    self.profile_photo_url = profile_photo_url
    self.cover_photo_url = cover_photo_url
    self.photos = []

  @property
  def first_name(self) -> str:
    return self._first_name

  @property
  def last_name(self) -> str:
    return self._last_name

  @property
  def full_name(self) -> str:
    first, last = self.first_name, self.last_name
    if first is None:
      return last
    if last is None:
      return first
    return " ".join([first, last])

  @property
  def path(self) -> str:
    """Returns the path of the folder that contains the profile's photos."""
    return os.path.join(self.database_path, self.id)

  def describe(self):
    print("Facebook ID:", self.id)
    print("Name:", self.full_name)
    print("Hometown:", self.hometown)
    print("Current city:", self.current_city)

  def to_dict(self) -> Dict[str, Any]:
    param_keys = set(inspect.signature(self.__init__).parameters.keys())
    param_dict = {k: getattr(self, k) for k in param_keys}

    param_dict["about_dict"] = dict(self.about_dict)
    param_dict["photos_main_url"] = [p.main_page_url for p in self.photos]
    param_dict["photos_large_url"] = [p.large_photo_url for p in self.photos]
    param_dict["photos_neighbor_urls"] = [p.neighbor_urls for p in self.photos]

    return dict(param_dict)


class ScrapableFacebookProfile(FacebookProfile):

  def scrape(self, session: facebook.FacebookSession, sleep_time: int = 1):
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

  def download_next_photo(self, session: facebook.FacebookSession,
                          sleep_time: int = 1):
    if self.photos:
      # Downloading the photo that is right after the last downloaded photo
      if not self.photos[-1].is_downloaded:
        print("WARNING: Photo {} of {} is not downloaded locally."
              "".format(self.photos[-1].id, self.id))
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
      new_photo = photos.ScrapableFacebookPhoto(photo_url, self.path)
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
