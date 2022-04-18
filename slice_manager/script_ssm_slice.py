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

names = ['core']
actions = ['registry', 'start', 'reconfig', 'create', 'modify', 'remove', 'registration',
           'handover', 'deregistration']

SSM_ID = {}

lock = asyncio.Lock()
liveWebSockets = {}

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

  def check_origin(self, origin):
    return True


  async def on_message(self, message): #pylint: disable=invalid-overridden-method
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

      if name == names[0]:
        liveWebSockets[sfuuid] = self

      # only for test case
      #toSend = message_dict
      #LOG.info("tosend = " + str(toSend))
      #toSendJson = json.dumps(toSend)
      #LOG.info("send new message " + toSendJson)
      #self.write_message(toSendJson)
    # start
    elif action == actions[1]:
      sfuuid = SSM_ID[_id]

    # create
    elif action == actions[3]:
      #TODO
      for sfuuid in liveWebSockets:

        to_send = {"name": "core", "id": sfuuid, "action": action,
                   "info": message_dict['info']}
        to_send_json = json.dumps(to_send)
        LOG.info(name + ": send new message to SSM" + to_send_json)

        liveWebSockets[sfuuid].write_message(to_send_json)

      to_send = {"name": name, "id": _id, "action": action,
                 "message": "Create OK"}
      LOG.info(name + ": to_send = " + str(to_send))
      to_send_json = json.dumps(to_send)
      LOG.info(name + ": send new message " + to_send_json)
      self.write_message(to_send_json)

    # modify
    elif action == actions[4]:
      #TODO
      for sfuuid in liveWebSockets:

        to_send = {"name": "core", "id": sfuuid, "action": action,
                   "info": message_dict['info']}
        to_send_json = json.dumps(to_send)
        LOG.info(name + ": send new message to SSM" + to_send_json)

        liveWebSockets[sfuuid].write_message(to_send_json)

      to_send = {"name": name, "id": _id, "action": action,
                 "message": "Modify OK"}
      LOG.info(name + ": to_send = " + str(to_send))
      to_send_json = json.dumps(to_send)
      LOG.info(name + ": send new message " + to_send_json)
      self.write_message(to_send_json)

    # remove
    elif action == actions[5]:
      #TODO
      for sfuuid in liveWebSockets:

        to_send = {"name": "core", "id": sfuuid, "action": action,
                   "info": message_dict['info']}
        to_send_json = json.dumps(to_send)
        LOG.info(name + ": send new message to SSM" + to_send_json)

        liveWebSockets[sfuuid].write_message(to_send_json)

      to_send = {"name": name, "id": _id, "action": action,
                 "message": "Remove OK"}
      LOG.info(name + ": to_send = " + str(to_send))
      to_send_json = json.dumps(to_send)
      LOG.info(name + ": send new message " + to_send_json)
      self.write_message(to_send_json)

    # registration
    elif action == actions[6]:
      #TO#DO script to activate proxy arp.
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
      for sfuuid in liveWebSockets:

        to_send = {"name": "core", "id": sfuuid, "action": action,
                   "info": message_dict['info']}
        to_send_json = json.dumps(to_send)
        LOG.info(name + ": send new message to SSM" + to_send_json)

        liveWebSockets[sfuuid].write_message(to_send_json)

      to_send = {"name": name, "id": _id, "action": action,
                 "message": "Registration OK"}
      LOG.info(name + ": to_send = " + str(to_send))
      to_send_json = json.dumps(to_send)
      LOG.info(name + ": send new message " + to_send_json)
      self.write_message(to_send_json)

    # handover
    elif action == actions[7]:
      #TODO
      for sfuuid in liveWebSockets:

        to_send = {"name": "core", "id": sfuuid, "action": action,
                   "info": message_dict['info']}
        to_send_json = json.dumps(to_send)
        LOG.info(name + ": send new message to UE SSM" + to_send_json)

        liveWebSockets[sfuuid].write_message(to_send_json)

      # Estimate time for the handover be applied.
      time.sleep(2)

      to_send = {"name": name, "id": _id, "action": action,
                 "message": "Handover OK"}
      LOG.info(name + ": to_send = " + str(to_send))
      to_send_json = json.dumps(to_send)
      LOG.info(name + ": send new message " + to_send_json)
      self.write_message(to_send_json)

    # deregistration
    elif action == actions[8]:
      #TODO
      for sfuuid in liveWebSockets:

        to_send = {"name": "core", "id": sfuuid, "action": action,
                   "info": message_dict['info']}
        to_send_json = json.dumps(to_send)
        LOG.info(name + ": send new message to SSM" + to_send_json)

        liveWebSockets[sfuuid].write_message(to_send_json)

      to_send = {"name": name, "id": _id, "action": action,
                 "message": "Deregistration OK"}
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
