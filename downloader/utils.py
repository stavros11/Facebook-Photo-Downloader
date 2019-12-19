"""Utilities for loading files."""
import pickle
import os
import pandas as pd
from typing import List


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
