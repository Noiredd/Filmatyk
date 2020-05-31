from threading import Thread
from tkinter import messagebox

import hashlib
import json
import os
import shutil
from urllib.parse import urljoin

import requests
from semantic_version import Version
Timeout = requests.urllib3.connection.ConnectTimeoutError

class Paths(object):
  meta_file         = "VERSION.json"
  temp_dir          = "__update__"
  local_repo_path   = ".."
  release_repo_path = "https://raw.githubusercontent.com/Noiredd/Filmatyk/stable/"
  debug_repo_path   = "https://raw.githubusercontent.com/Noiredd/Filmatyk/prerelease/"

class Updater(object):
  update_ready_string = "Aktualizacja dostępna"
  update_question_string = "Czy zaktualizować teraz?"
  update_failed_header = "Aktualizacja nieudana"
  update_failed_string = "Nie udało się pobrać nowych plików. Spróbuj później."
  max_download_attempts = 3

  def __init__(self, root, version_string, progress=None, quitter=None, debugMode=False, linuxMode=False):
    self.tkroot = root
    self.version = Version(version_string)
    self.progress = progress
    self.quitter = quitter
    self.debugMode = debugMode
    self.linuxMode = linuxMode
    self.checked_flag = False
    self.update_available = False
    # get correct path constants for release/debug mode
    self.local_meta_file_path = os.path.join(Paths.local_repo_path, Paths.meta_file)
    self.temporary_directory = os.path.join(Paths.local_repo_path, Paths.temp_dir)
    self.remote_repository_path = (
      Paths.release_repo_path if not debugMode else
      Paths.debug_repo_path
    )
    self.remote_meta_file_path = urljoin(self.remote_repository_path, Paths.meta_file)

  # REMOTE INTERFACE
  def pullFile(self, path, relative=True, timeout=5.0, encoding=None):
    """ Downloads a file from a given path and returns its content as string.
        The path can be either relative to the remote repo, or absolute.
    """
    if relative:
      path = path.replace('\\', '/') # Windows-style to URL-style
      path = urljoin(self.remote_repository_path, path)
    try:
      response = requests.get(path, timeout=timeout)
    except Timeout:
      return None
    # server should respond with OK (200) code - if not, abort
    if response.status_code != 200:
      return None
    if encoding is None:
      return response.content # return raw bytes
    else:
      return str(response.content, encoding=encoding)

  # CHECKING FOR AN UPDATE
  def checkUpdates(self):
    # start a background thread to actually check for updates
    self.thread = Thread(target=self.__checkUpdates)
    self.thread.start()
    # start a polling loop to check for the thread completion
    self.__checkThread()
  def __checkThread(self):
    if self.checked_flag:
      # thread has finished - clean up and do something with the results
      self.thread.join()
      if self.update_available:
        doUpdate = messagebox.askyesno(self.update_ready_string, self.update_question_string)
        if doUpdate:
          self.performUpdate()
    else:
      # not done yet - try again in a while
      self.tkroot.after(200, self.__checkThread)
  def __checkUpdates(self):
    # perform the actual update check within a separate thread
    raw_metadata = self.pullFile(self.remote_meta_file_path, relative=False, encoding='utf-8')
    if not raw_metadata:
      # null response - kill self
      self.checked_flag = True
      return
    metadata = json.loads(raw_metadata)
    self.new_version = Version(metadata['version'])
    self.updated_files = metadata['files']
    # set the flags and exit
    if self.new_version > self.version:
      self.update_available = True
    self.checked_flag = True

  # PERFORMING AN UPDATE
  def performUpdate(self):
    existing_files = self.getExistingFiles()
    download_files = self.getDownloadFiles(existing_files)
    deletion_files = self.getDeletionFiles(existing_files)
    # in debug mode, show the lists of changes first
    if self.debugMode:
      print("About to download:")
      for item in download_files:
        print('  {} ({:.8})'.format(item[0], item[1]))
      if deletion_files:
        print("About to remove:")
        for item in deletion_files:
          print('  {}'.format(item))
    # prepare the temp directory, progress bar etc.
    if not os.path.isdir(self.temporary_directory):
      os.mkdir(self.temporary_directory)
    n_files = len(download_files)
    update_successful = True
    self.progress(0)
    # try to download each file
    for i, f_tuple in enumerate(download_files):
      new_file, new_sum = f_tuple
      success = self.downloadFile(new_file, new_sum)
      if success:
        perc_done = (100. * (i + 1)) / n_files
        self.progress(perc_done)
      else:
        update_successful = False
        break
    # apply a successful update
    if update_successful:
      self.removeOldBackups() # clean up after any previous updates
      # overwrite files with downloaded versions
      for new_file, _ in download_files:
        self.applyFile(new_file)
      # "delete" (actually backup) files marked for removal by the new verion
      for del_file in deletion_files:
        del_file = os.path.join(Paths.local_repo_path, del_file)
        shutil.move(del_file, del_file + '.bak')
      # update the version file ONLY when succeeded
      self.updateVersionFile()
    # clean up and restart the app or display an error message
    shutil.rmtree(self.temporary_directory)
    self.progress(-1) # hide the bar
    if update_successful:
      self.quitter(restart=True)
    else:
      messagebox.showerror(self.update_failed_header, self.update_failed_string)
  def getExistingFiles(self):
    """ Reads the current version file and returns the dict of files. """
    with open(self.local_meta_file_path, 'r') as current_ver_file:
      current_ver_data = json.loads(current_ver_file.read())
    return current_ver_data['files']
  def getDownloadFiles(self, existing):
    """ Returns dict of files to be downloaded (new or changed ones). """
    download_list = []
    for new_file, new_sum in self.updated_files.items():
      if not new_file in existing.keys():
        download_list.append((new_file, new_sum)) # new
      elif new_sum != existing[new_file]:
        download_list.append((new_file, new_sum)) # changed
    return download_list
  def getDeletionFiles(self, existing):
    """ Returns list of files that are removed in the new version. """
    return [
      ex_file for ex_file in existing.keys()
      if ex_file not in self.updated_files.keys()
    ]
  def downloadFile(self, path, checksum, attempt=1):
    """ Downloads a file from a repo-relative path to a temporary location.
        Retries if the checksum doesn't match (up to 3 attempts)."""
    # download raw data
    data = self.pullFile(path)
    # save in the temp location
    target_path = os.path.join(
      self.temporary_directory,
      path.replace("\\", "--")
    )
    with open(target_path, 'wb') as target:
      target.write(data)
    # validate checksum (after saving - be sure the file was properly written)
    try:
      with open(target_path, 'r', encoding='utf-8') as d_file:
        stored_data = d_file.read()
      stored_bytes = bytes(stored_data, encoding='utf-8')
    except UnicodeDecodeError:
      # binary file won't decode to UTF - read bytes directly
      with open(target_path, 'rb') as d_file:
        stored_bytes = d_file.read()
    hasher = hashlib.sha256()
    hasher.update(stored_bytes)
    check = hasher.hexdigest()
    # success/retry/failure logic
    if check == checksum:
      return True # correctly downloaded
    else:
      if attempt < self.max_download_attempts:
        self.downloadFile(path, checksum, attempt=attempt+1) # try again
      else:
        return False  # repetitive failure
  def removeOldBackups(self, path=Paths.local_repo_path):
    """ Recursively traverses the app directory and removes any .bak files. """
    folders = []
    for item in os.listdir(path):
      ipath = os.path.join(path, item)
      if os.path.isdir(ipath):
        folders.append(ipath)
      elif ipath.endswith('.bak'):
        os.remove(ipath)
    for folder in folders:
      self.removeOldBackups(path=folder)
  def applyFile(self, path):
    """ Moves a file from a temp location overwriting the target file.
        Accepts repo-relative paths. Backs up the original file first."""
    # Path to the file in a temporary directory
    source_path = os.path.join(
      self.temporary_directory,
      path.replace("\\", "--")
    )
    # Path to its destination in the app directory tree
    target_path = os.path.join(
      "..", path if not self.linuxMode else path.replace("\\", "/")
    )
    # If the file already exists in the app - back it up first
    if os.path.exists(target_path):
      backup_path = target_path + ".bak"
      shutil.move(target_path, backup_path)
    else:
      # If it doesn't, perhaps the owning folder doesn't either
      parent = os.path.split(target_path)[0]
      if not os.path.exists(parent):
        os.makedirs(parent)
    # Finally, move the updated file over
    shutil.move(source_path, target_path)
  def updateVersionFile(self):
    updated_data = {
      'version': str(self.new_version),
      'files': self.updated_files
    }
    with open(self.local_meta_file_path, 'w', encoding='utf-8') as updated_ver_file:
      updated_ver_file.write(json.dumps(updated_data, indent=2, sort_keys=True))
