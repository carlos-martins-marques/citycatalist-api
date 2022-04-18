#!/usr/local/bin/python3.4
"""
## Database Module
"""

from threading import Lock


"""
Database model
{
  "<5gName>": {
    "status": "<status>"
    }
  }
}
""" # pylint: disable=pointless-string-statement

class FiveGDatabase:
  """ Class to store references to all 5G Systems """

  def __init__(self):
    self.slice_db = dict()
    self.lock = Lock()

  def add_5g(self, name):
    """ Creates a new 5G System with the given name """
    self.lock.acquire()
    if name in self.slice_db:
      self.lock.release()
      raise ValueError("Error while adding s5G Systemlice \""+ name + "\": Already exists!")

    slice_entry = dict()
    slice_entry["status"] = "CREATING"
    self.slice_db[name] = slice_entry
    self.lock.release()

  def del_5g(self, name):
    """ Deletes the 5G System with that name """
    self.lock.acquire()
    if not name in self.slice_db:
      self.lock.release()
      raise ValueError("Error while deleting 5G System \""+ name + "\": Not exists!")

    #del self.slice_db[name]
    self.slice_db.pop(name)
    self.lock.release()

  def update_status_5g(self, status, name):
    """ Updates the 5G System with that status for the given name """
    self.lock.acquire()
    if not name in self.slice_db:
      self.lock.release()
      raise ValueError("Error while updating 5G System \""+ name + "\": Not exists!")

    self.slice_db[name]["status"] = status

    self.lock.release()

  def get_status_5g(self, name):
    """ Returns the status of slice """

    if not name in self.slice_db:
      raise ValueError("Error while geting status 5G System \""+ name + "\": Not exists!")

    return self.slice_db[name]["status"]

  def get_5g(self, name):
    """ Returns the 5G System (object) to perform operations in that 5G System """

    if not name in self.slice_db:
      raise ValueError("Error while geting 5G System \""+ name + "\": Not exists!")

    return self.slice_db[name]

  def get_all_5g(self):
    """ Returns the 5G System database (object) to perform operations """

    return self.slice_db

"""
Database model
{
  "<sliceName>": {
    "status": "<status>",
    "sliceName": "<sliceName>",
    "5gName": "<5gName>",
    "ueIds": ["<ueIds>"],
    "gnbIds": ["<gnbIds>"],
    "requirements: {
      "bandwidth": "<bandwidth>",
      "delay":"<delay>", 
      "priority":"<priority>",
      "reliability":"< reliability>"
    }
  }
}
"""

class SliceDatabase:
  """ Class to store references to all slices """

  def __init__(self):
    self.slice_db = dict()
    self.lock = Lock()

  def add_slice(self, name, nsi_json):
    """ Creates a new slice with the given name """
    self.lock.acquire()
    if name in self.slice_db:
      self.lock.release()
      raise ValueError("Error while adding slice \""+ name + "\": Already exists!")

    slice_entry = nsi_json
    slice_entry["status"] = "CREATING"
    self.slice_db[name] = slice_entry
    self.lock.release()

  def mod_slice(self, slice_name, nsi_json):
    """ Modify a slice with the given name """
    self.lock.acquire()
    if not slice_name in self.slice_db:
      self.lock.release()
      raise ValueError("Error while modifying slice \""+ slice_name +
                       "\": Not exists!")

    if "ueIds" in nsi_json:
      self.slice_db[slice_name]["ueIds"] = nsi_json["ueIds"]

    if "gnbIds" in nsi_json:
      self.slice_db[slice_name]["gnbIds"] = nsi_json["gnbIds"]

    self.lock.release()

  def del_slice(self, name):
    """ Deletes the slice with that name """
    self.lock.acquire()
    if not name in self.slice_db:
      self.lock.release()
      raise ValueError("Error while deleting slice \""+ name + "\": Not exists!")

    #del self.slice_db[name]
    self.slice_db.pop(name)
    self.lock.release()

  def update_status_slice(self, status, name):
    """ Updates the slice with that status for the given name """
    self.lock.acquire()
    if not name in self.slice_db:
      self.lock.release()
      raise ValueError("Error while updating slice \""+ name + "\": Not exists!")

    self.slice_db[name]["status"] = status

    self.lock.release()

  def get_status_slice(self, name):
    """ Returns the status of slice """

    if not name in self.slice_db:
      raise ValueError("Error while geting status slice \""+ name + "\": Not exists!")

    return self.slice_db[name]["status"]

  def get_slice(self, name):
    """ Returns the slice (object) to perform operations in that slice """

    if not name in self.slice_db:
      raise ValueError("Error while geting slice \""+ name + "\": Not exists!")

    return self.slice_db[name]

  def get_all_slices(self):
    """ Returns the slice database (object) to perform operations """

    return self.slice_db
