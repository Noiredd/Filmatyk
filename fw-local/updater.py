from threading import Thread
from tkinter import messagebox

import hashlib
import json
import os
import shutil

import requests
from semantic_version import Version
Timeout = requests.urllib3.connection.ConnectTimeoutError

class Paths(object):
  local_meta_file   = "..\\VERSION.json"
  local_temp_dir    = "..\\__update__"
  remote_repo_path  = "https://raw.githubusercontent.com/Noiredd/fw-local/v{}/"
  release_meta_path = "https://raw.githubusercontent.com/Noiredd/fw-local/master/VERSION.json"
  debug_meta_path   = "https://raw.githubusercontent.com/Noiredd/fw-local/prerelease/VERSION.json"

class Updater(object):
  update_ready_string = "Aktualizacja dostępna"
  update_question_string = "Czy zaktualizować teraz?"
  update_failed_header = "Aktualizacja nieudana"
  update_failed_string = "Nie udało się pobrać nowych plików. Spróbuj później."
  max_download_attempts = 3

  def __init__(self, root, version_string, progress=None, quitter=None, debugMode=False):
    self.tkroot = root
    self.version = Version(version_string)
    self.progress = progress
    self.quitter = quitter
    self.debugMode = debugMode
    self.checked_flag = False
    self.update_available = False
    # get correct path constants for release/debug mode
    self.local_meta_file_path = Paths.local_meta_file
    self.temporary_directory = Paths.local_temp_dir
    self.remote_repository_path = Paths.remote_repo_path
    self.remote_meta_file_path = (
      Paths.release_meta_path if not debugMode else
      Paths.debug_meta_path
    )

  # REMOTE INTERFACE
  def pullFile(self, path, relative=True, timeout=5.0, encoding=None):
    """ Downloads a file from a given path and returns its content as string.
        The path can be either relative to the remote repo, or absolute.
    """
    if relative:
      path = self.remote_repository_path + path.replace('\\', '/')
    try:
      response = requests.get(path, timeout=timeout)
    except Timeout:
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
      # thread has finished - do something with the results
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
    # read the existing file list
    with open(self.local_meta_file_path, 'r') as current_ver_file:
      current_ver_data = json.loads(current_ver_file.read())
    current_files = current_ver_data['files']
    # specify the path to the exact release to download
    self.remote_repository_path = self.remote_repository_path.format(
      str(self.new_version)
    )
    # prepare the list of files do download
    download_list = [] # (path, checksum) tuples
    # compare each new file with the existing
    for new_file, new_sum in self.updated_files.items():
      if not new_file in current_files.keys():
        download_list.append((new_file, new_sum))
      elif new_sum != current_files[new_file]:
        download_list.append((new_file, new_sum))
    # try to download each file
    if not os.path.isdir(self.temporary_directory):
      os.mkdir(self.temporary_directory)
    n_files = len(download_list)
    update_successful = True
    self.progress(0)  # display the progress bar
    for i, f_tuple in enumerate(download_list):
      new_file, new_sum = f_tuple
      success = self.downloadFile(new_file, new_sum)
      if success:
        perc_done = (100. * (i + 1)) / n_files
        self.progress(perc_done)
      else:
        update_successful = False
        break
    # in debug mode, show the list of things to update
    if self.debugMode:
      print("About to download:")
      for item in download_list:
        print('  {}'.format(item))
    # apply a successful update
    if update_successful:
      # move all files from the temp area to their destinations
      for new_file, _ in download_list:
        self.applyFile(new_file)
      # update the version file ONLY when succeeded
      self.updateVersionFile()
    # clean up and restart the app or display an error message
    shutil.rmtree(self.temporary_directory)
    self.progress(-1) # hide the bar
    if update_successful:
      self.quitter(restart=True)
    else:
      messagebox.showerror(self.update_failed_header, self.update_failed_string)
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
    with open(target_path, 'r', encoding='utf-8') as d_file:
      stored_data = d_file.read()
    hasher = hashlib.sha256()
    hasher.update(bytes(stored_data, encoding='utf-8'))
    check = hasher.hexdigest()
    # success/retry/failure logic
    if check == checksum:
      return True # correctly downloaded
    else:
      if attempt < self.max_download_attempts:
        self.downloadFile(path, checksum, attempt=attempt+1) # try again
      else:
        return False  # repetitive failure
  def applyFile(self, path):
    """ Moves a file from a temp location overwriting the target file.
        Accepts repo-relative paths. Backs up the original file first."""
    source_path = os.path.join(
      self.temporary_directory,
      path.replace("\\", "--")
    )
    target_path = os.path.join("..", path)
    backup_path = target_path + ".bak"
    # back up the original file
    shutil.move(target_path, backup_path)
    # move the updated file over
    shutil.move(source_path, target_path)
  def updateVersionFile(self):
    updated_data = {
      'version': str(self.new_version),
      'files': self.updated_files
    }
    with open(self.local_meta_file_path, 'w', encoding='utf-8') as updated_ver_file:
      updated_ver_file.write(json.dumps(updated_data, indent=2, sort_keys=True))
