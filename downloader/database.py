"""Data structure for collection of facebook profiles."""
import os
import pandas as pd
from downloader import facebook
from downloader import profiles
from typing import Optional, Set


class DatabaseError(Exception):
  """Raised when inconsistencies in database files are found."""
  pass


class Database:
  """Collection of scraped Facebook profiles."""

  def __init__(self,
               path: str,
               previous_data: Optional[pd.DataFrame] = None):
    """Creates database on a specific os path.

    Args:
      path: Path where folders that contain photos will be located.
        The database is saved as a pd.DataFrame named `profiles.pkl` in the
        same path.
      previous_data: DataFrame loaded from an already existing `profiles.pkl`.
    """
    self.path = path
    self.new_data = []

    self.fb_session = None
    self.sleep_time = 1
    self.max_photos = 5

    if previous_data is None:
      self._existing_ids = set()
      print("Existing database not found. Will create a new database in {}."
            "".format(path))
    else:
      self._existing_ids = set(previous_data["id"])
    self.previous_data = previous_data

  @property
  def existing_ids(self) -> Set[str]:
    """Returns a set with profile IDs that exist in the database."""
    return self._existing_ids

  @property
  def existing_folders(self) -> Set[str]:
    """Returns a set with the name of folders that exist in the path."""
    return set(next(os.walk(self.path))[1])

  @classmethod
  def load(cls, path: str) -> "Database":
    """Loads an existing database.

    Also checks if the loaded database is valid, by checking if the folders
    that exist in path are consistend with the IDs contained in the DataFrame.
    If `profiles.pkl` is not found a new database is created.
    """
    walker = os.walk(path)
    _, existing_folders, existing_files = next(walker)
    existing_folders = set(existing_folders)
    existing_files = set(existing_files)

    if not existing_folders:
      if "profiles.pkl" in existing_files:
        raise FileExistsError("profiles.pkl exists in {} while no folders "
                              "were found in the same directory.".format(path))
      return cls(path)

    if "profiles.pkl" not in existing_files:
      raise FileNotFoundError("Failed to find profiles.pkl in {}."
                              "".format(path))

    existing_data = pd.read_pickle(os.path.join(path, "profiles.pkl"))
    database = cls(path, previous_data=existing_data)
    database.check()
    return database

  def set_session(self,
                  facebook_session: facebook.FacebookSession,
                  max_photos: int = 5,
                  sleep_time: int = 1):
    """Sets the parameters of the scraping session."""
    self.fb_session = facebook_session
    self.sleep_time = sleep_time
    self.max_photos = max_photos

  def add(self, profile_id: str):
    """Scrapes and adds a profile in the database."""
    if profile_id in self.existing_ids:
      print("\nSkipping {} because it exists in database.".format(profile_id))
      return

    profile = profiles.ScrapableFacebookProfile(profile_id, self.path)
    if os.path.exists(profile.path):
      raise FileExistsError("Found folder for {} while this ID does not "
                              "exist in the database.".format(profile_id))

    print("\nAttempting to scrape {}.".format(profile_id))

    os.mkdir(profile.path)
    try:
      self.scrape(profile)
      self._existing_ids.add(profile_id)
    # TODO: Fix exceptions
    except Exception as error:
      print("Failed to scrape {} with {}.".format(profile_id, error))
      if os.listdir(profile.path):
        raise FileExistsError("Directory of {} is not empty and database "
                              "will be corrupted.".format(profile_id))
      os.rmdir(profile.path)

  def scrape(self, profile: profiles.ScrapableFacebookProfile):
    """Attempts to scrape a profile and download its photos."""
    # Scrape profile information and photo links
    profile.scrape(self.fb_session, self.sleep_time)
    # Download photos
    while len(profile.photos) < self.max_photos:
      try:
        profile.download_next_photo(self.fb_session, self.sleep_time)
      except NameError:
        break
      if profile.photos[-1].next_url is None:
        break
    self.new_data.append(profile.to_dict())
    print("{} scraped successfully with {} photos.".format(profile.id, len(profile.photos)))

  def save(self):
    """Saves the database as `profiles.pkl` in path."""
    if self.previous_data is None:
      total_data = pd.DataFrame(self.new_data)
    else:
      new_data = pd.DataFrame(self.new_data)
      total_data = pd.concat([self.previous_data, new_data], ignore_index=True, sort=True)
    total_data.to_pickle(os.path.join(self.path, "profiles.pkl"))

  def check(self):
    """Checks whether a saved database is valid.

    Asserts that the folders existing in path are consistend with the IDs
    contained in the DataFrame.
    """
    ids, folders = self.existing_ids, self.existing_folders
    if ids != folders:
      raise DatabaseError("Loaded database is invalid. Found folders for "
                          "{} ids while pickle contains {}."
                          "".format(folders, ids))
