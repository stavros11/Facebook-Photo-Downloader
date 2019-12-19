"""Main downloading script."""
import os
import argparse
import time
import pandas as pd
import downloader

from typing import List, Optional


def main(friends_file: str,
         max_photos: int,
         email: str, password: str,
         data_dir: Optional[str] = None,
         start: int = 0,
         end: Optional[int] = None,
         sleep_time: int = 1,
         sleep_between: int = 4):
  # Read profile ids from given file
  profile_ids = downloader.read_friend_list(friends_file)
  print("Found {} profile ids.".format(len(profile_ids)))
  profile_ids = profile_ids[start: end]
  print("Indexed profile ids from {} to {}.".format(start, end))
  print("Will attempt to scrape {} profile ids.".format(len(profile_ids)))

  if data_dir is None:
    data_dir, _ = os.path.split(friends_file)
  print("\nSaving directory is set to {}.".format(data_dir))

  # Check if database exists
  database_dir = os.path.join(data_dir, "profiles.pkl")
  try:
    database = pd.read_pickle(database_dir)
    print("\nLoaded existing database from {}.".format(database_dir))
    scrapped_ids = set(database["id"])
    print("{} profiles already in database.".format(len(scrapped_ids)))
  except:
    database = None
    scrapped_ids = set()
    print("Existing database not found. Will create a new database in {}."
          "".format(database_dir))

  print("\nAttempting to scrape {} profiles with {} photos each.".format(
      len(profile_ids), max_photos))

  # Log in to facebook
  fb_session = downloader.FacebookSession()
  fb_session.login(email, password)
  print("Logged in to facebook using {}.".format(email))
  time.sleep(sleep_between)

  data = []
  for profile_id in profile_ids:
    profile_dir = os.path.join(data_dir, profile_id)

    # Check if profile already exists in database
    if profile_id in scrapped_ids:
      print("\nSkipping {} because it exists in database.".format(profile_id))
      if not os.path.isdir(profile_dir):
        raise FileNotFoundError("Profile ID {} exists in database but ")
      continue

    try:
      print("\nAttempting to scrape {}.".format(profile_id))
      if not os.path.exists(profile_dir):
        os.mkdir(profile_dir)

      profile = downloader.ScrapableFacebookProfile(
          profile_id, local_photo_dir=profile_dir)

      # Scrape profile information and photo links
      profile.scrape(fb_session, sleep_time)
      # Download photos
      while len(profile.photos) < max_photos:
        try:
          profile.download_next_photo(fb_session, sleep_time)
        except NameError:
          break
        if profile.photos[-1].next_url is None:
          break

      data.append(dict(profile.to_dict()))
      print("{} scraped successfully with {} photos.".format(
          profile_id, len(profile.photos)))
      time.sleep(sleep_between)

    # TODO: Fix exceptions
    except Exception as e:
      print("Failed to scrape {}.".format(profile_id))
      try:
        # Remove folder
        os.rmdir(profile_dir)
      except OSError:
        print("Failed to remove directory {}.".format(profile_dir))


  # Save data to pkl
  if database is None:
    new_database = pd.DataFrame(data)
  else:
    new_database = pd.concat([database, pd.DataFrame(data)], ignore_index=True,
                              sort=True)
  new_database.to_pickle(database_dir)
  return


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--friends-file", default="", type=str)
  parser.add_argument("--data-dir", default=None, type=str)
  parser.add_argument("--max-photos", default=5, type=int)
  parser.add_argument("--start", default=0, type=int)
  parser.add_argument("--end", default=None, type=int)
  parser.add_argument("--email", default=None, type=str)
  parser.add_argument("--password", default=None, type=str)
  parser.add_argument("--sleep-time", default=2, type=int)
  parser.add_argument("--sleep-between", default=5, type=int)

  main(**vars(parser.parse_args()))
