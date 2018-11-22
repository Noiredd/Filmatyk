import os
import requests_html

class PosterManager():
  CACHE_DIR = os.path.join('..', 'cache')
  NO_POSTER = 'https://2.fwcdn.pl/gf/beta/ic/plugs/v01/fNoImg140.jpg'

  def __init__(self):
    self.session = requests_html.HTMLSession()
    self.cached = []
    # create the cache folder if necessary
    if not os.path.exists(self.CACHE_DIR):
      os.mkdir(self.CACHE_DIR)
    elif not os.path.isdir(self.CACHE_DIR):
      os.remove(self.CACHE_DIR)
      os.mkdir(self.CACHE_DIR)
    else:
      self.cached = [int(os.path.splitext(f)[0]) for f in os.listdir(self.CACHE_DIR)]
    # acquire the blank poster icon
    if 0 not in self.cached:
      self.downloadPoster(self.NO_POSTER, self.makePosterPath(0))
      self.cached.append(0)
  def makePosterPath(self, pid:int):
    return os.path.join(self.CACHE_DIR, '{}.png'.format(pid))
  def downloadPoster(self, url:str, path:str):
    # downloads from url, stores under path
    response = self.session.get(url)
    if not response.ok:
      return False
    with open(path, 'wb') as ifile:
      ifile.write(response.content)
    return True
  def getPosterByURL(self, url:str):
    if not url:
      return self.makePosterPath(0)
    # URL is like: 'https://1.fwcdn.pl/po/60/10/796010/7814354.6.jpg'
    # "796010" is actually the item ID -- can be used for caching
    splits = url.split('/')
    pid = int(splits[-2])
    # if such poster ID has been cached - retrieve it
    if pid in self.cached:
      return self.makePosterPath(pid)
    else:
      # otherwise, try downloading it
      path = self.makePosterPath(pid)
      if not self.downloadPoster(url, path):
        # on failure, return the default, blank poster
        return self.makePosterPath(0)
      # on success - remember to add to cached
      self.cached.append(pid)
      return path
