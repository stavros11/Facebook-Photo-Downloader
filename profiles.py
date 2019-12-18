"""Basic data structures for profiles and photos."""
import os
import inspect
from typing import Any, Dict, Optional, Tuple


class FacebookProfile:
  """Base profile data structure."""

  def __init__(self,
               id: str,
               first_name: Optional[str] = None,
               last_name: Optional[str] = None,
               hometown: Optional[str] = None,
               current_city: Optional[str] = None,
               profile_photo_url: Optional[str] = None,
               cover_photo_url: Optional[str] = None,
               local_photo_dir: Optional[str] = None):
    # Basic information
    self.id = id
    self._first_name = first_name
    self._last_name = last_name

    # Information found in about page
    self.hometown = hometown
    self.current_city = current_city
    self.about_dict = {}
    # Photos
    self.profile_photo_url = profile_photo_url
    self.cover_photo_url = cover_photo_url
    self.local_photo_dir = local_photo_dir
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

    return param_dict


class FacebookPhoto:
  """Base photo data structure."""

  def __init__(self,
               main_page_url: str,
               large_photo_url: Optional[str] = None,
               local_dir: Optional[str] = None,
               local_encoding_file_dir: Optional[str] = None,
               local_encoding_ind: Optional[int] = None):
    self.id = self.find_photo_id(main_page_url)
    self.local_dir = local_dir
    self.local_encoding_file_dir = local_encoding_file_dir
    self.local_encoding_ind = local_encoding_ind

    self.main_page_url = main_page_url
    self.large_photo_url = large_photo_url

    self._previous = None
    self._next = None

    self.facebook_page_url = None
    self.facebook_large_photo_url = None

  @property
  def previous_url(self) -> str:
    return self._previous

  @property
  def next_url(self) -> str:
    return self._next

  @property
  def neighbor_urls(self) -> Tuple[str, str]:
    return (self._previous, self._next)

  @property
  def filename(self) -> str:
    """Creates the local file name for the photo."""
    return ".".join([self.id, "jpg"])

  @property
  def is_downloaded(self) -> bool:
    return self.filename in set(os.listdir(self.local_dir))

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
