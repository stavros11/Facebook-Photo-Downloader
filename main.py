"""Main downloading script."""
import pickle
import os
import argparse
import time
import downloader

from typing import List, Optional


def read_friend_list(file_dir: str) -> List[str]:
  """Reads profile IDs to scrape from file.

  Supported files are `pkl` that represents a Python list of strings or
  a `txt` in which each line contains a profile ID.

  Args:
    file_dir: Path of the file that contains profile IDs.

  Returns:
    List with profile IDs.
  """
  file_type = file_dir.split(".")[-1]
  if file_type == "pkl":
    with open(file_dir, "rb") as file:
      profile_ids = pickle.load(file)
  elif file_type == "txt":
    with open(file_dir, "r") as file:
      profile_ids = [x.replace("\n", "").replace(" ", "")
                     for x in file.readlines()]
  else:
    raise NotImplementedError("Friend list should be of pkl or txt type "
                              "but a {} file was given.".format(file_type))
  return profile_ids


def main(friends_file: str,
         max_photos: int,
         email: str, password: str,
         data_dir: Optional[str] = None,
         sleep_time: int = 1,
         sleep_between: int = 4,
         start: int = 0,
         end: Optional[int] = None):
  """Runs photo downloader.

  Args:
    friends_file: Full directory of a file that contains the facebook IDs of
      the people that we want to download the photos of.
      See `read_friend_list` for details on what kinds of files are currently
      supported.
    max_photos: Maximum number of photos to download from each person.
    email: Email of the facebook account to use for login.
    password: Password of the facebook account for login.
    data_dir: Full path to save database files and folders with photos.
      If `data_dir` is not given, the directory that contains `friends_file`
      is used automatically.
    sleep_time: Awaiting time between HTTP requests when scrapping a single
      profile.
    sleep_between: Awaiting time between scrapping the next profile.
    start, end: Optional indexing of the list read in `friends_file`.
  """
  # Read profile ids from given file
  profile_ids = read_friend_list(friends_file)
  print("Found {} profile ids.".format(len(profile_ids)))
  profile_ids = profile_ids[start: end]
  print("Indexed profile ids from {} to {}.".format(start, end))

  print("\nAttempting to scrape {} profiles with {} photos "
        "each.".format(len(profile_ids), max_photos))

  if data_dir is None:
    data_dir, _ = os.path.split(friends_file)
  print("\nSaving directory is set to {}.".format(data_dir))

  # Load database
  database = downloader.Database.load(data_dir)

  # Log in to facebook
  fb_session = downloader.facebook.FacebookSession()
  fb_session.login(email, password)
  print("Logged in to facebook using {}.".format(email))
  database.set_session(fb_session, max_photos, sleep_time)
  time.sleep(sleep_between)

  # Scrape profiles and add them to database
  for profile_id in profile_ids:
    database.add(profile_id)

  # Save data to pkl
  database.save()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--friends-file", default="", type=str)
  parser.add_argument("--data-dir", default=None, type=str)
  parser.add_argument("--max-photos", default=5, type=int)
  parser.add_argument("--start", default=0, type=int)
  parser.add_argument("--end", default=None, type=int)
  parser.add_argument("--email", default=None, type=str)
  parser.add_argument("--password", default=None, type=str)
  parser.add_argument("--sleep-time", default=1, type=int)
  parser.add_argument("--sleep-between", default=3, type=int)
  main(**vars(parser.parse_args()))
