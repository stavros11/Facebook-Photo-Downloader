"""Logged-in facebook session."""
import time
import requests
from typing import Optional


class FacebookSession:
  """Requests logged-in facebook session."""

  def __init__(self, session: Optional[requests.session] = None,
               base_url="https://m.facebook.com"):
    self.base_url = base_url
    if session is None:
      self.session = requests.session()
    else:
      self.session = session

  def login(self, email: str, password: str):
    """Login to facebook using an email and password."""
    self.session.headers.update(
        {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:39.0) Gecko/20100101 Firefox/39.0'})

    # Navigate to Facebook's homepage to load Facebook's cookies.
    self.session.get(self.base_url)
    # Attempt to login to Facebook
    self.session.post('{}/login.php'.format(self.base_url),
                      data={'email': email, 'pass': password},
                      allow_redirects=False)

  def _get(self, url, **kwargs):
    """Implements `get` and `get_large_photo`."""
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
    """Requests a facebook page.

    Args:
      link: URL of the page to send the request for.
      attempts: Number of attempts to get the page.
      retry_time: Awaiting time between attempts.

    Returns:
      The HTTP response to our request.
    """
    url = "/".join([self.base_url, link])
    return self._get(url, attempts=attempts, retry_time=retry_time)

  def get_large_photo(self, url, attempts: int = 5, retry_time: int = 5):
    """Requests a large photo page.

    See `get` for more details.
    """
    return self._get(url, attempts=attempts, retry_time=retry_time,
                     stream=True)
