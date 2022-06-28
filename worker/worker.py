#!/usr/local/bin/python3.4
"""
## Copyright (c) 2015 SONATA-NFV, 2017 5GTANGO [, ANY ADDITIONAL AFFILIATION]
## ALL RIGHTS RESERVED.
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##
## Neither the name of the SONATA-NFV, 5GTANGO [, ANY ADDITIONAL AFFILIATION]
## nor the names of its contributors may be used to endorse or promote
## products derived from this software without specific prior written
## permission.
##
## This work has been performed in the framework of the SONATA project,
## funded by the European Commission under Grant number 671517 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the SONATA
## partner consortium (www.sonata-nfv.eu).
##
## This work has been performed in the framework of the 5GTANGO project,
## funded by the European Commission under Grant number 761493 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the 5GTANGO
## partner consortium (www.5gtango.eu).
"""

import logging
import datetime
import time
import json
from threading import Thread, Lock

import interfaces.sbi as sbi
import database.database as database
from logger import TangoLogger

from slice_manager.client_script_ssm_slice import client_ssm_thread

# INFORMATION
# mutex used to ensure one single access to ddbb (repositories) for the nsi records
#  creation/update/removal
mutex_slice2db_access = Lock()

#Log definition to make the slice logs idetified among the other possible 5GTango components.
LOG = TangoLogger.getLogger(__name__, log_level=logging.DEBUG, log_json=True)
TangoLogger.getLogger("citycatalistApi:worker", logging.DEBUG, log_json=True)
LOG.setLevel(logging.DEBUG)

db_5g = database.FiveGDatabase()

db = database.SliceDatabase()

################################ THREADs to manage slice requests #################################
# SEND NETWORK SLICE (NS) INSTANTIATION REQUEST
## Objctive: send request 2 GTK to instantiate
## Params: nsi - parameters given by the user.
class ThreadNsInstantiate(Thread):
  def __init__(self, nsi_json):
    Thread.__init__(self)
    self.nsi = {}
    self.req = nsi_json

  # Creates the json structure to request a NS instantiation.
  def send_instantiation_request(self):
    LOG.info("Instantiating Slice: " + self.req['5gName'])

    # NS requests information
    data = {}
    data['name'] = self.req['5gName']
    data['nst_id'] = self.req['5gTemplateId']
    data['request_type'] = 'CREATE_SLICE'
    if self.req['instantiation_params']:
      data['instantiation_params'] = self.req['instantiation_params']

    # Calls the function towards the GTK
    LOG.info("NS Instantiation request JSON: " + str(data))
    instantiation_response = sbi.net_serv_instantiate(data)
    return instantiation_response
    #return ({},201)


  def run(self):

    # Store slice
    db_5g.add_5g(self.req['5gName'])



    # acquires mutex to have unique access to the nsi (repositories)
    mutex_slice2db_access.acquire()

    instantiation_resp = self.send_instantiation_request()
    if instantiation_resp[1] != 201:
      self.nsi['nsi-status'] = 'ERROR'
      self.nsi['errorLog'] = 'ERROR when instantiating '
      # Change status
      db_5g.update_status_5g("ERROR", self.req['5gName'])

    else:
      self.nsi['id'] = self.req['5gName']
      self.nsi['nsi-status'] = 'INSTANTIATING'
      # Change status
      db_5g.update_status_5g("CREATING", self.req['5gName'])


    # releases mutex for any other thread to acquire it
    mutex_slice2db_access.release()

    if self.nsi['nsi-status'] != 'ERROR':
      # Waits until the NS is instantiated/ready or error
      deployment_timeout = 30 * 60   # 30 minutes

      nsi_instantiated = False
      while deployment_timeout > 0:

        if self.nsi['id'] == self.req['5gName']:
          uuid = sbi.get_nsi_id_from_name(self.req['5gName'])
          if uuid:
            self.nsi['id'] = uuid

        if self.nsi['id'] != self.req['5gName']:
          # Check ns instantiation status
          nsi = sbi.get_saved_nsi(self.nsi['id'])
          if "uuid" in nsi:
            self.nsi = nsi
            self.nsi["id"] = self.nsi["uuid"]
            del self.nsi["uuid"]

          if self.nsi['nsi-status'] in ["INSTANTIATED", "ERROR", "READY"]:
            nsi_instantiated = True

          # if all services are instantiated, ready or error, break the while loop to notify the GTK
          if nsi_instantiated:
            LOG.info("Network Slice Instantiation request processed for Network Slice with ID: "+
                     str(self.nsi['id']))
            # Change status
            db_5g.update_status_5g("CREATED", self.req['5gName'])
            break

        time.sleep(15)
        deployment_timeout -= 15

      if not nsi_instantiated:
        self.nsi['nsi-status'] = 'ERROR'
        self.nsi['errorLog'] = 'ERROR when terminating with timeout'
        # Change status
        db_5g.update_status_5g("ERROR", self.req['5gName'])


# SEND NETWORK SLICE (NS) TERMINATION REQUEST
## Objctive: send the ns termination request 2 GTK
## Params: nsiId (uuid within the incoming request URL)
class ThreadNsTerminate(Thread):
  def __init__(self, nsi, name):
    Thread.__init__(self)
    self.nsi = nsi
    self.req = name

  def send_termination_requests(self):
    LOG.info("Terminating Slice: ")

    data = {}
    data["instance_uuid"] = self.nsi['id']
    data["request_type"] = "TERMINATE_SLICE"

    # calls the function towards the GTK
    termination_response = sbi.net_serv_terminate(data)

    return termination_response[0], termination_response[1]
    #return ({},201)

  def run(self):

    # acquires mutex to have unique access to the nsi (repositories)
    mutex_slice2db_access.acquire()

    # Change status
    db_5g.update_status_5g("DELETING", self.req)

    # sends each of the termination requests
    LOG.info("Termination Step: Terminating Network Slice Instantiation.")

    # requests to terminate a nsi
    termination_resp = self.send_termination_requests()
    if termination_resp[1] != 201:
      self.nsi['nsi-status'] = 'ERROR'
      self.nsi['errorLog'] = 'ERROR when terminating '
      # Change status
      db_5g.update_status_5g("ERROR", self.req)

    # releases mutex for any other thread to acquire it
    mutex_slice2db_access.release()

    if self.nsi['nsi-status'] != 'ERROR':
      # Waits until the NS is terminated or error
      deployment_timeout = 30 * 60   # 30 minutes

      nsi_terminated = False
      while deployment_timeout > 0:
        # Check ns instantiation status
        self.nsi = sbi.get_saved_nsi(self.nsi['id'])

        self.nsi["id"] = self.nsi["uuid"]
        del self.nsi["uuid"]

        if self.nsi['nsi-status'] in ["TERMINATED", "ERROR"]:
          nsi_terminated = True

        # if slice is terminated or error, break the while loop to notify the GTK
        if nsi_terminated:
          LOG.info("Network Slice Termination request processed for Network Slice with ID: "+
                   str(self.nsi['id']))
          # Change status
          db_5g.update_status_5g("DELETED", self.req)
          break

        time.sleep(15)
        deployment_timeout -= 15

      if not nsi_terminated:
        self.nsi['nsi-status'] = 'ERROR'
        self.nsi['errorLog'] = 'ERROR when terminating with timeout'
        # Change status
        db_5g.update_status_5g("ERROR", self.req)



################################ SLICE CREATION SECTION ##################################

# Does all the process to Create the Slice
def create_5g(nsi_json):
  LOG.info("Check for NstID before instantiating it.")
  nst_id = nsi_json['5gTemplateId']
  catalogue_response = sbi.get_saved_nst(nst_id)
  if catalogue_response.get('nstd'):
    nst_json = catalogue_response['nstd']
  else:
    return catalogue_response, catalogue_response['http_code']

  # validate if there is any NSTD
  if not catalogue_response:
    return_msg = {}
    return_msg['error'] = "There is NO Slice Template with this uuid in the DDBB."
    return return_msg, 400

  # check if exists another nsir with the same name (5gName)
  nsirepo_jsonresponse = sbi.get_all_saved_nsi()
  if nsirepo_jsonresponse:
    for nsir_item in nsirepo_jsonresponse:
      if nsir_item["name"] == nsi_json['5gName']:
        return_msg = {}
        return_msg['error'] = "There is already an 5G System with this name."
        return (return_msg, 400)

    # Network Slice Placement
  LOG.info("Placement of the Network Service Instantiations.")
  new_nsi_json = nsi_placement(nsi_json, nst_json)

  if new_nsi_json[1] != 200:
    LOG.info("Error returning saved nsir.")
    return (new_nsi_json[0], new_nsi_json[1])

  # starts the thread to instantiate while sending back the response
  LOG.info("Network Slice Instance Record created. Starting the instantiation procedure.")
  thread_ns_instantiation = ThreadNsInstantiate(new_nsi_json[0])
  thread_ns_instantiation.start()

  #return 201
  return ({}, 201)

# does the NS placement based on the available VIMs resources & the required of each NS.
def nsi_placement(nsi_json, nst_json):

  # get the VIMs information registered to the SP
  vims_list = sbi.get_vims_info()

  # validates if the incoming vim_list is empty (return 500) or not (follow)
  if 'vim_list' not in vims_list:
    return_msg = {}
    return_msg['error'] = "Not found any VIM information, register one to the SP."
    return return_msg, 500

  # NSR PLACEMENT: placement based on the instantiation parameters...
  vim_id = ""
  if 'location' in nsi_json:
    for vim_item in vims_list['vim_list']:
      if (vim_item['type'] == "vm" and vim_item['vim_uuid'] == nsi_json['location']):
        vim_id = vim_item['vim_uuid']
        break
  else:
    # TODO For when vim_id is not specified in the api
    city = "IT"
    for vim_item in vims_list['vim_list']:
      if (vim_item['type'] == "vm" and vim_item['vim_city'] == city):
        vim_id = vim_item['vim_uuid']
        break

  if vim_id != "":
    instantiation_params_list = []
    for subnet_item in nst_json["slice_ns_subnets"]:
      service_dict = {}
      service_dict["vim_id"] = vim_id
      service_dict["subnet_id"] = subnet_item["id"]
      instantiation_params_list.append(service_dict)
    nsi_json['instantiation_params'] = json.dumps(instantiation_params_list)

  return nsi_json, 200

#################################### SLICE DELETION SECTION #######################################

# Does all the process to delete the 5G System
def delete_5g(name):
  #LOG.info("Updating the Network Slice Record for the termination procedure.")
  mutex_slice2db_access.acquire()
  try:
    # Get the uuid form the name provided
    uuid = sbi.get_nsi_id_from_name(name)
    if uuid:
      terminate_nsi = sbi.get_saved_nsi(uuid)
      if terminate_nsi:
        # if nsi is not in TERMINATING/TERMINATED
        if terminate_nsi['nsi-status'] in ["INSTANTIATED", "INSTANTIATING", "READY", "ERROR"]:
          terminate_nsi['id'] = terminate_nsi['uuid']
          del terminate_nsi['uuid']

          terminate_nsi['terminateTime'] = str(datetime.datetime.now().isoformat())
          #terminate_nsi['sliceCallback'] = TerminOrder['callback']
          terminate_nsi['nsi-status'] = "TERMINATING"

          # starts the thread to terminate while sending back the response
          LOG.info("Starting the termination procedure.")
          thread_ns_termination = ThreadNsTerminate(terminate_nsi, name)
          thread_ns_termination.start()

          #return 204 for slice
          terminate_value = 204


        else:
          terminate_nsi['errorLog'] = "This Slice is either terminated or being terminated."
          terminate_value = 404
      else:
        terminate_nsi['errorLog'] = "There is no Slice with this name in the db."
        terminate_value = 404
    else:
      terminate_nsi = {}
      terminate_nsi['errorLog'] = "There is no Slice with this name in the db."
      terminate_value = 404
  finally:
    mutex_slice2db_access.release()

  return (terminate_nsi, terminate_value)

########################################## CREATE SLICE SECTION ##################################

# Does all the process to create the slice
def create_slice(nsi_json, slice_name):
  LOG.info("Create Slice")

  #TODO Order Slice Creation in 5G
  # choose the best slice id based in re"quirements
  if int(nsi_json["requirements"]["bandwidth"]) < 10:
    slice_id="3"
  elif int(nsi_json["requirements"]["bandwidth"]) < 85:
    slice_id="4"
  elif int(nsi_json["requirements"]["bandwidth"]) < 110:
    slice_id="1"
  else:
    slice_id="2"

  nsi_json["sliceType"]=slice_id
  # Change status
  db.add_slice(slice_name, nsi_json)
  dict_message = {"name":"api", "id":"", "action":"create",
                  "info": {"sliceType":nsi_json["sliceType"],"ueIds":nsi_json["ueIds"]}}
  #threading.Thread(target=client_ssm_thread,args=(dict_message,)).start()
  message = client_ssm_thread(dict_message)
  db.update_status_slice("CREATED", slice_name)

  return ({"message": message}, 201)

########################################## MODIFY SLICE SECTION ##################################

# Does all the process to modify the slice
def modify_slice(nsi_json, slice_name):
  LOG.info("Modify Slice")

  # Change status
  db.update_status_slice("MODIFYING", slice_name)
  #TODO Order Slice Mofification in 5G
  # see the diferences add new users and remove old users
  old_ue_ids = db.get_slice(slice_name)["ueIds"]
  rm_ue_ids = []
  add_ue_ids = []
  for ue_id in old_ue_ids:
    if ue_id not in nsi_json["ueIds"]:
      rm_ue_ids.append(ue_id)

  for ue_id in nsi_json["ueIds"]:
    if ue_id not in old_ue_ids:
      add_ue_ids.append(ue_id)

  #dict_message = {"name":"api", "id":"", "action":"modify", "slice":slice_name,
  #                "info":nsi_json}
  #threading.Thread(target=client_ssm_thread,args=(dict_message,)).start()
  message=""
  if add_ue_ids:
    dict_message_c = {"name":"api", "id":"", "action":"create",
                  "info": {"sliceType":db.get_slice(slice_name)["sliceType"],"ueIds":add_ue_ids}}
    message = client_ssm_thread(dict_message_c)
  if rm_ue_ids:
    dict_message_r = {"name":"api", "id":"", "action":"remove",
                  "info": {"sliceType":db.get_slice(slice_name)["sliceType"],"ueIds":rm_ue_ids}}
    message = client_ssm_thread(dict_message_r)
  db.mod_slice(slice_name, nsi_json)
  db.update_status_slice("MODIFIED", slice_name)

  return ({"message": message}, 201)



###################################### REMOVE SLICE SECTION #######################################

# Does all the process to remove the slice
def remove_slice(slice_name):
  LOG.info("Remove Slice")

  # Change status
  db.update_status_slice("REMOVING", slice_name)
  nsi_json=db.get_slice(slice_name)
  #TODO Order Slice Removal in 5G
  dict_message = {"name":"api", "id":"", "action":"remove",
                  "info": {"sliceType":nsi_json["sliceType"],"ueIds":nsi_json["ueIds"]}}
  #threading.Thread(target=client_ssm_thread,args=(dict_message,)).start()
  message = client_ssm_thread(dict_message)
  db.update_status_slice("REMOVED", slice_name)

  return ({"message": message}, 204)

###################################### Registration SECTION #######################################

# Does all the process to registration the UE
def registration(nsi_json, slice_name):
  LOG.info("Registration UE")

  # Change status
  db.update_status_slice("UNDER_REGISTRATION", slice_name)
  # Order Registration
  dict_message = {"name":"api", "id":"", "action":"registration",
                  "info":nsi_json}
  #threading.Thread(target=client_ssm_thread,args=(dict_message,)).start()
  message = client_ssm_thread(dict_message)
  # Change status
  db.update_status_slice("FINISHED_REGISTRATION", slice_name)
  return ({"message": message}, 202)

########################################## HANDOVER SECTION #######################################

# Does all the process to handover the UE between Edges
def handover(nsi_json, slice_name):
  LOG.info("Handover UE")

  # Change status
  db.update_status_slice("UNDER_HANDOVER", slice_name)
  # Order Handover
  dict_message = {"name":"api", "id":"", "action":"handover",
                  "info":nsi_json}
  #threading.Thread(target=client_ssm_thread,args=(dict_message,)).start()
  message = client_ssm_thread(dict_message)
  # Change status
  db.update_status_slice("FINISHED_HANDOVER", slice_name)
  return ({"message": message}, 202)

# Status options
""" public enum Status {

	CREATING,
	CREATED,
	ADDING,
  ADDED,
  UNDER_REGISTRATION,
  FINISHED_REGISTRATION,
  UNDER_HANDOVER,
  FINISHED_HANDOVER,
  REMOVING,
  REMOVED,
	DELETING,
	DELETED,
	ERROR
	
} """ # pylint: disable=pointless-string-statement

###################################### Deregistration SECTION ######################################

# Does all the process to deregistration the UE
def deregistration(nsi_json, slice_name):
  LOG.info("Deregistration UE")

  # Change status
  db.update_status_slice("UNDER_DEREGISTRATION", slice_name)
  # Order Deregistration
  dict_message = {"name":"api", "id":"", "action":"deregistration",
                  "info":nsi_json}
  #threading.Thread(target=client_ssm_thread,args=(dict_message,)).start()
  message = client_ssm_thread(dict_message)
  # Change status
  db.update_status_slice("FINISHED_DEREGISTRATION", slice_name)
  return ({"message": message}, 202)

########################################## STATUS SECTION #######################################

# Does all the process to get the 5G System status
"""
Database model
{
  "<5gName>": {
    "status": "<status>"
  }
}

Return
{
  "5gName": "<5gName>",
  "status": "<status>"
}
"""

def get_5g_status(slice_name):
  LOG.info("Get 5G System Status")
  slice_status = {}

  # Check if 5g exists
  all_slice_info = db_5g.get_all_5g()
  if not slice_name in all_slice_info:
    return (slice_status, 404)

  # Get status for a specific 5g
  slice_info = all_slice_info[slice_name]

  if slice_info:
    slice_status["5gName"] = slice_name
    slice_status["status"] = slice_info["status"]

  return (slice_status, 200)

# Does all the process to get the status of all 5G Systems
"""
Database model
{
  "<5gName>": {
    "status": "<status>"
  }
}

Return
[
  {
    "5gName": "<5gName>",
    "status": "<status>",
  },
  ...
]
"""

def get_all_5g_status():
  LOG.info("Get All 5G System Status")

  # Get status for all 5G System
  all_slice_status = []
  all_slice_info = db_5g.get_all_5g()
  for slice_name in all_slice_info:

    slice_status = {}
    slice_info = all_slice_info[slice_name]

    slice_status["5gName"] = slice_name
    slice_status["status"] = slice_info["status"]

    all_slice_status.append(slice_status)

  return (all_slice_status, 200)


# Does all the process to get the status
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


Return
{
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
"""

def get_slice_status(slice_name):
  LOG.info("Get Slice Status")
  slice_status = {}

  # Check if slice exists
  all_slice_info = db.get_all_slices()
  if not slice_name in all_slice_info:
    return (slice_status, 404)

  # Get status for a specific slice
  slice_info = db.get_slice(slice_name)

  if slice_info:
    slice_status = slice_info

  return (slice_status, 200)

# Does all the process to get the status of all slices
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

Return
[
  {
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
  },
  ...
]
"""

def get_all_slice_status():
  LOG.info("Get All Slice Status")

  # Get status for all slices
  all_slice_status = []
  all_slice_info = db.get_all_slices()
  for slice_name in all_slice_info:

    slice_status = {}
    slice_info = all_slice_info[slice_name]
    slice_status = slice_info

    all_slice_status.append(slice_status)

  return (all_slice_status, 200)
