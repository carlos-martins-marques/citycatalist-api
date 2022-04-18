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

from flask import Flask, request, jsonify
#from tornado import websocket, web, ioloop, httpserver
#from slice_manager.script_ssm_slice import app_ssm

import worker.worker as worker
import interfaces.validate_incoming_json as json_validator
from logger import TangoLogger

#Log definition to make the slice logs idetified among the other possible 5GTango components.
LOG = TangoLogger.getLogger(__name__, log_level=logging.DEBUG, log_json=True)
TangoLogger.getLogger("citycatalistApi:nbi", logging.DEBUG, log_json=True)
LOG.setLevel(logging.DEBUG)

app = Flask(__name__)

#Variables with the API path sections
API_ROOT = "/api"
API_VERSION = "/v1"
API_SLICE = "/slice"
API_5G = "/5g"


################################ CITYCATALIST API Actions #########################################
# CREATES a 5G System
@app.route(API_ROOT+API_VERSION+API_5G, methods=['POST'])
def create_slice():
  LOG.info("Request to create a 5G System with the following information: " + str(request.json))

  # validates the fields with uuids (if they are right UUIDv4 format), 400 Bad request / 201 ok
  creating_5g = json_validator.validate_create_5g(request.json)

  if creating_5g[1] == 200:
    creating_5g = worker.create_5g(request.json)

  return jsonify(creating_5g[0]), creating_5g[1]


# CREATES a Slice
@app.route(API_ROOT+API_VERSION+API_SLICE+'/<name>/action/create', methods=['POST'])
def create_slice_subnet(name):
  LOG.info("Request to create a Slice with the following information: " + str(request.json))

  # validates the fields with uuids (if they are right UUIDv4 format), 400 Bad request / 201 ok
  creating_slice = json_validator.validate_create_slice(request.json)

  if creating_slice[1] == 200:
    creating_slice = worker.create_slice(request.json, name)

  return jsonify(creating_slice[0]), creating_slice[1]

# Modify a Slice
@app.route(API_ROOT+API_VERSION+API_SLICE+'/<name>/action/modify', methods=['PUT'])
def add_slice_subnet(name):
  LOG.info("Request to modify the Slice according to the following: " + str(request.json))

  # validates the fields with uuids (if they are right UUIDv4 format), 400 Bad request / 202 ok
  modify_slice = json_validator.validate_modify_slice(request.json)

  if modify_slice[1] == 200:
    modify_slice = worker.modify_slice(request.json, name)

  return jsonify(modify_slice[0]), modify_slice[1]

# Registration
@app.route(API_ROOT+API_VERSION+API_SLICE+'/<name>/action/registration', methods=['PUT'])
def registration(name):
  LOG.info("Request to registration according to the following: " + str(request.json))

  # validates the fields with uuids (if they are right UUIDv4 format), 400 Bad request / 202 ok
  _registration = json_validator.validate_registration(request.json)
  #_registration = ("", 200)

  if _registration[1] == 200:
    _registration = worker.registration(request.json, name)

  return jsonify(_registration[0]), _registration[1]

# Handover
@app.route(API_ROOT+API_VERSION+API_SLICE+'/<name>/action/handover', methods=['PUT'])
def handover(name):
  LOG.info("Request to handover according to the following: " + str(request.json))

  # validates the fields with uuids (if they are right UUIDv4 format), 400 Bad request / 202 ok
  _handover = json_validator.validate_handover(request.json)
  #_handover = ("", 200)

  if _handover[1] == 200:
    _handover = worker.handover(request.json, name)

  return jsonify(_handover[0]), _handover[1]

# Deregistration
@app.route(API_ROOT+API_VERSION+API_SLICE+'/<name>/action/deregistration', methods=['PUT'])
def deregistration(name):
  LOG.info("Request to delete the Slice Subnet according to the following: " + str(request.json))

  # validates the fields with uuids (if they are right UUIDv4 format), 400 Bad request / 202 ok
  _deregistration = json_validator.validate_deregistration(request.json)

  if _deregistration[1] == 200:
    _deregistration = worker.deregistration(request.json, name)

  return jsonify(_deregistration[0]), _deregistration[1]

# REMOVES a Slice
@app.route(API_ROOT+API_VERSION+API_SLICE+'/<name>/action/remove', methods=['DELETE'])
def remove_slice(name):
  LOG.info("Request to remove the Slice according to the following: " + str(request.json))

  # validates the fields with uuids (if they are right UUIDv4 format), 400 Bad request / 204 ok
  #removing_slice = json_validator.validate_remove_slice(request.json)

  #if removing_slice[1] == 200:
  removing_slice = worker.remove_slice(name)

  return jsonify(removing_slice[0]), removing_slice[1]

# DELETE a 5G System
@app.route(API_ROOT+API_VERSION+API_5G+'/<name>', methods=['DELETE'])
def delete_slice(name):
  LOG.info("Request to delete a 5G System with the following information: " + str(request.json))

  # validates the fields with uuids (if they are right UUIDv4 format), 400 Bad request / 204 ok
  #deleting_5g = json_validator.validate_delete_5g(request.json)

  #if deleting_5g[1] == 200:
  deleting_5g = worker.delete_5g(name)

  return jsonify(deleting_5g[0]), deleting_5g[1]

# GETS s specific 5G System Status
@app.route(API_ROOT+API_VERSION+API_5G+'/<name>/status', methods=['GET'])
def get_5g_status(name):
  LOG.info("Request to retreive all the Slice Status.")
  _5g_status = worker.get_5g_status(str(name))

  return jsonify(_5g_status[0]), _5g_status[1]

# GETS a SPECIFIC Slice Status
@app.route(API_ROOT+API_VERSION+API_SLICE+'/<name>/status', methods=['GET'])
def get_slice_status(name):
  LOG.info("Request to retrieve the Slice Status with Name: " + str(name))
  _slice_status = worker.get_slice_status(str(name))

  return jsonify(_slice_status[0]), _slice_status[1]
