"""
#
"""

import json
import logging
import time
import asyncio
import os
import requests
#from tornado import websocket, web, ioloop, httpserver
from tornado import websocket, web
#import paramiko # type: ignore # pylint: disable=import-error


LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

names = ['access', 'core', 'ue']
actions = ['registry', 'start', 'reconfig', 'registration', 'handover', 'add', 'remove']
DATA_A = {}
DATA_C = {}
DATA_U = {}
SSM_ID = {}
ACCESS_SSM = 2
SSM = 0
MAX_SSM = 2 + ACCESS_SSM
lock = asyncio.Lock()
liveWebSockets = {}
ueWebSockets = {}
UE_ID = 2

def get_status(service_id):
  status = ''
  ip_address = os.environ.get("SONATA_API")
  port = os.environ.get("SONATA_API_PORT")
  #ip_address = "193.136.92.119"
  #port = "32002"
  url = "http://"+ip_address+":"+port+"/api/v3/records/services/"+service_id
  response = requests.get(url)
  if response.ok:
    response_dict = json.loads(response.text)
    status = response_dict["status"]
  else:
    LOG.warning("Status request return code: " + str(response.status_code))
    #response.raise_for_status()

  return status

class WSHandler(websocket.WebSocketHandler): #pylint: disable=abstract-method

  def __init__(self, *args, **kwargs): #pylint: disable=useless-super-delegation
    super().__init__(*args, **kwargs)

  def open(self):  #pylint: disable=arguments-differ
    LOG.info('New connection')


  def on_close(self):
    LOG.info('Connection closed')
    for key, value in liveWebSockets.items():
      if self == value:
        liveWebSockets.pop(key)
        break
    for key, value in ueWebSockets.items():
      if self == value:
        ueWebSockets.pop(key)
        break
  def check_origin(self, origin):
    return True


  async def on_message(self, message): #pylint: disable=invalid-overridden-method
    global DATA_A  #pylint: disable=global-statement
    global DATA_C  #pylint: disable=global-statement
    global DATA_U  #pylint: disable=global-statement
    global SSM     #pylint: disable=global-statement
    global SSM_ID  #pylint: disable=global-statement
    global UE_ID   #pylint: disable=global-statement
    global MAX_SSM #pylint: disable=global-statement
    LOG.info('message received:  %s' % message)

    message_dict = json.loads(message)
    name = message_dict['name']
    _id = message_dict['id']
    action = message_dict['action']

    LOG.info("Received action: " + action)

    # registry
    if action == actions[0]:
      sfuuid = message_dict['sfuuid']
      SSM_ID[_id] = sfuuid

      liveWebSockets[sfuuid] = self

      if name == names[2]:
        ueWebSockets[sfuuid] = self

      # only for test case
      #toSend = message_dict
      #LOG.info("tosend = " + str(toSend))
      #toSendJson = json.dumps(toSend)
      #LOG.info("send new message " + toSendJson)
      #self.write_message(toSendJson)
    # start
    elif action == actions[1]:
      sfuuid = SSM_ID[_id]
      data_m = message_dict['data']

      if name == names[0]:
        async with lock:
          order = len(DATA_A) + 1
          for vnf in data_m:
            for interface in vnf["ifdata"]:
              interface.update({'id':_id})
              if vnf["name"] in ["vnf-open5gcorer5-gnb", "vnf-open5gcorer5-upfe",
                                 "vnf-open5gcorer5-igwe"]:
                interface["ifid"] = interface["ifid"][0:5].replace("1", str(order)) + \
                                    interface["ifid"][5:]

          DATA_A[sfuuid] = data_m
      elif name == names[1]:
        for vnf in data_m:
          for interface in vnf["ifdata"]:
            interface.update({'id':_id})
        DATA_C[sfuuid] = data_m

      else:
        async with lock:
          order = len(DATA_U) + 1
          for vnf in data_m:
            for interface in vnf["ifdata"]:
              interface.update({'id':_id})
              if vnf["name"] in ["vnf-open5gcorer5-ue"]:
                interface["ifid"] = interface["ifid"][0:5].replace("1", str(order)) + \
                                    interface["ifid"][5:]
          DATA_U[sfuuid] = data_m

      # Wait for have the start of all ssm to reconfig
      while (len(DATA_A) + len(DATA_C) + len(DATA_U)) < MAX_SSM:
        LOG.info(name + "-" + sfuuid + ": wait start for others ssm")
        await asyncio.sleep(1)

      # Wait for the service be ready
      for sv_id in DATA_A:
        while True:
          status = get_status(sv_id)
          if status == "normal operation":
            break
          LOG.info(name + "-" + sfuuid + ": wait for service access-" + sv_id + " be ready")
          await asyncio.sleep(5)

      for sv_id in DATA_C:
        while True:
          status = get_status(sv_id)
          if status == "normal operation":
            break
          LOG.info(name + "-" + sfuuid + ": wait for service core-" + sv_id + " be ready")
          await asyncio.sleep(5)

      for sv_id in DATA_U:
        while True:
          status = get_status(sv_id)
          if status == "normal operation":
            break
          LOG.info(name + "-" + sfuuid + ": wait for service ue-" + sv_id + " be ready")
          await asyncio.sleep(5)

      LOG.info(name + "-" + sfuuid + ": wait 60 seconds after all services ready")
      await asyncio.sleep(60)

      data_to_send = []
      for sv_id in DATA_A:
        data_to_send += DATA_A[sv_id]
      for sv_id in DATA_C:
        data_to_send += DATA_C[sv_id]
      for sv_id in DATA_U:
        data_to_send += DATA_U[sv_id]
      to_send = {"name": name, "id": _id, "action": actions[2],
                 "data": data_to_send}
      LOG.info(name + "-" + sfuuid + ": tosend = " + str(to_send))
      to_send_json = json.dumps(to_send)
      LOG.info(name + "-" + sfuuid + ": send new message " + to_send_json)
      self.write_message(to_send_json)
      SSM += 1
      if SSM == MAX_SSM:
        SSM = 0
        DATA_A = {}
        DATA_C = {}
        DATA_U = {}
        SSM_ID = {}
        UE_ID = 2

    # registration
    elif action == actions[3]:
      #TODO script to activate proxy arp.
      # url:193.136.92.183 u:altice p:ecitla
      #/bin/bash /opt/stack/script_arp_proxy.sh
      #client = paramiko.SSHClient()
      #client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      #client.connect('193.136.92.183', username='altice', password='ecitla')

      #stdin, stdout, stderr = client.exec_command('/bin/bash /opt/stack/script_arp_proxy.sh')  #pylint: disable=unused-variable

      #for line in stdout:
      #  LOG.info(line.strip('\n'))

      #client.close()

      #TODO
      for sfuuid in ueWebSockets:

        to_send = {"name": "ue", "id": sfuuid, "action": "registration"}
        to_send_json = json.dumps(to_send)
        LOG.info(name + ": send new message to UE SSM" + to_send_json)

        ueWebSockets[sfuuid].write_message(to_send_json)
      # Get the sfuuid of UE and send the message
      #liveWebSockets[sfuuid].write_message(message)

      to_send = {"name": name, "id": _id, "action": action,
                 "message": "Registration OK"}
      LOG.info(name + ": to_send = " + str(to_send))
      to_send_json = json.dumps(to_send)
      LOG.info(name + ": send new message " + to_send_json)
      self.write_message(to_send_json)

    # handover
    elif action == actions[4]:
      #TODO
      for sfuuid in ueWebSockets:

        to_send = {"name": "ue", "id": sfuuid, "action": "handover",
                   "edge": str(UE_ID)}
        to_send_json = json.dumps(to_send)
        LOG.info(name + ": send new message to UE SSM" + to_send_json)

        ueWebSockets[sfuuid].write_message(to_send_json)
      # Get the sfuuid of UE and send the message
      #liveWebSockets[sfuuid].write_message(message)
      if UE_ID == 2:
        UE_ID = 1
      else:
        UE_ID = 2

      # Estimate time for the handover be applied.
      time.sleep(2)

      to_send = {"name": name, "id": _id, "action": action,
                 "message": "Handover OK"}
      LOG.info(name + ": to_send = " + str(to_send))
      to_send_json = json.dumps(to_send)
      LOG.info(name + ": send new message " + to_send_json)
      self.write_message(to_send_json)

    # add
    elif action == actions[5]:
      #TODO
      # Get the sfuuid of service and send the message
      #liveWebSockets[sfuuid].write_message(message)
      to_send = {"name": name, "id": _id, "action": action,
                 "message": "Add OK"}
      LOG.info(name + ": to_send = " + str(to_send))
      to_send_json = json.dumps(to_send)
      LOG.info(name + ": send new message " + to_send_json)
      self.write_message(to_send_json)

    # remove
    elif action == actions[6]:
      #TODO
      # Get the sfuuid of service and send the message
      #liveWebSockets[sfuuid].write_message(message)
      to_send = {"name": name, "id": _id, "action": action,
                 "message": "Remove OK"}
      LOG.info(name + ": to_send = " + str(to_send))
      to_send_json = json.dumps(to_send)
      LOG.info(name + ": send new message " + to_send_json)
      self.write_message(to_send_json)

    else:
      LOG.warning("Action not recognized: " + action)

app_ssm = web.Application([
    (r'/ssm', WSHandler),
])

""" if __name__ == '__main__':


  http_server = httpserver.HTTPServer(app_ssm)
  http_server.listen(4001)
  ioloop.IOLoop.instance().start() """
