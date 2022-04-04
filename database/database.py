#!/usr/local/bin/python3.4

"""
Database model
{
  "<sliceName>": {
    "status": "<status>",
    "sliceSubnetIds": {
      "<sliceSubnetName>": {
        "status": "<status>"
      }
    }
  }
}

"""

from threading import Lock

class SliceDatabase:
  """ Class to store references to all slices """

  def __init__(self):
    self.slice_db = dict()
    self.lock = Lock()

  def add_slice(self, name):
    """ Creates a new slice with the given name """
    self.lock.acquire()
    if name in self.slice_db:
      self.lock.release()
      raise ValueError("Error while adding slice \""+ name + "\": Already exists!")

    slice_entry = dict()
    slice_entry["status"] = "CREATING"
    self.slice_db[name] = slice_entry
    self.lock.release()

  def add_slice_subnet(self, name, slice_name):
    """ Creates a new slice subnet with the given name in the given slice_name """
    self.lock.acquire()
    if not slice_name in self.slice_db:
      self.lock.release()
      raise ValueError("Error while adding slice subnet to slice \""+ slice_name +
                       "\": Not exists!")

    if "sliceSubnetIds" in self.slice_db[slice_name]:
      if name in self.slice_db[slice_name]["sliceSubnetIds"]:
        self.lock.release()
        raise ValueError("Error while adding slice subnet \""+ name + "\": Already exists!")

    else:
      self.slice_db[slice_name].update({"sliceSubnetIds":{}})

    slice_subnet_entry = dict()
    slice_subnet_entry["status"] = "CREATING"
    self.slice_db[slice_name]["sliceSubnetIds"][name] = slice_subnet_entry

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

  def del_slice_subnet(self, name, slice_name):
    """ Deletes the slice subnet with that name in the given slice_name """
    self.lock.acquire()
    if not slice_name in self.slice_db:
      self.lock.release()
      raise ValueError("Error while deleting slice subnet from slice \""+ slice_name +
                       "\": Not exists!")

    if not "sliceSubnetIds" in self.slice_db[slice_name]:
      self.lock.release()
      raise ValueError("Error while deleting slice subnet \""+ name + "\" from slice: Not exists!")

    if not name in self.slice_db[slice_name]["sliceSubnetIds"]:
      self.lock.release()
      raise ValueError("Error while deleting slice subnet \""+ name + "\" from slice: Not exists!")

    self.slice_db[slice_name]["sliceSubnetIds"].pop(name)

    self.lock.release()

  def update_status_slice(self, status, name):
    """ Updates the slice with that status for the given name """
    self.lock.acquire()
    if not name in self.slice_db:
      self.lock.release()
      raise ValueError("Error while updating slice \""+ name + "\": Not exists!")

    self.slice_db[name]["status"] = status

    self.lock.release()

  def update_status_slice_subnet(self, status, name, slice_name):
    """ Updates the slice subnet with that status for the given name in the given slice_name """
    self.lock.acquire()
    if not slice_name in self.slice_db:
      self.lock.release()
      raise ValueError("Error while updating slice subnet from slice \""+ slice_name +
                       "\": Not exists!")

    if not "sliceSubnetIds" in self.slice_db[slice_name]:
      self.lock.release()
      raise ValueError("Error while updating slice subnet \""+ name + "\" from slice: Not exists!")

    if not name in self.slice_db[slice_name]["sliceSubnetIds"]:
      self.lock.release()
      raise ValueError("Error while updating slice subnet \""+ name + "\" from slice: Not exists!")

    self.slice_db[slice_name]["sliceSubnetIds"][name]["status"] = status

    self.lock.release()

  def get_status_slice(self, name):
    """ Returns the status of slice """

    if not name in self.slice_db:
      raise ValueError("Error while geting status slice \""+ name + "\": Not exists!")

    return self.slice_db[name]["status"]

  def get_status_slice_subnet(self, name, slice_name):
    """ Returns the status of slice subnet for the given name in the given slice_name """

    if not slice_name in self.slice_db:
      raise ValueError("Error while geting slice subnet from slice \""+ slice_name +
                       "\": Not exists!")

    if not "sliceSubnetIds" in self.slice_db[slice_name]:
      raise ValueError("Error while geting slice subnet \""+ name + "\" from slice: Not exists!")

    if not name in self.slice_db[slice_name]["sliceSubnetIds"]:
      raise ValueError("Error while geting slice subnet \""+ name + "\" from slice: Not exists!")

    return self.slice_db[slice_name]["sliceSubnetIds"][name]["status"]

  def get_slice(self, name):
    """ Returns the slice (object) to perform operations in that slice """

    if not name in self.slice_db:
      raise ValueError("Error while geting slice \""+ name + "\": Not exists!")

    return self.slice_db[name]

  def get_all_slices(self):
    """ Returns the slice database (object) to perform operations """

    return self.slice_db
