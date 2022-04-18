"""
## Client Web Socket for contact with SSM
"""

import sys
import json
#from queue import Queue
#import threading
import asyncio
import logging
import time
#from tornado import websocket, web, ioloop, httpserver, gen
from tornado import websocket, ioloop, gen

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

MESSAGE_RETURN = ""

class Client():

  def __init__(self, url, argv):
    self.url = url
    asyncio.set_event_loop(asyncio.new_event_loop())
    self.ioloop = ioloop.IOLoop.instance()
    self.connect(argv)
    #PeriodicCallback(self.keep_alive, 20000).start()
    self.ioloop.start()

  def message_received(self, message):
    global MESSAGE_RETURN #pylint: disable=global-statement
    LOG.info('message received...')
    logging.warning("*********************Handling message: "+message)

    # Format message
    message_dict = json.loads(message)
    message = message_dict['message']
    MESSAGE_RETURN = message

  def register(self, argv):
    try:

      #to_send = { "name": sv, "id": sv+"_SSM_0", "sfuuid": sv+"_service_id" , "action": "registry"}
      to_send = argv
      to_send_json = json.dumps(to_send)
      LOG.info("Sending register: " + str(to_send_json))
      self._ws.write_message(to_send_json)
    except Exception as err: #pylint: disable=broad-except
      LOG.error("Exception: " + str(err))

  """
  def reply_to_portal(self, name , id, action):
    to_send = {
      "action": "yet to start"
    }

    try:
      to_send_json = json.dumps(to_send)
      LOG.info("Sending reply: " + str(to_send_json))
      self._ws.write_message(to_send_json)
      LOG.info("Finished sending reply.")
    except Exception as e: #pylint: disable=broad-except
      LOG.error("Exception: " + str(e))
  """ # pylint: disable=pointless-string-statement

  @gen.coroutine
  def connect(self, argv=None):

    LOG.info("connecting to websocket..." + self.url)
    logging.warning("*********************Listening to Requests...!")
    connecting = True
    while connecting:
      try:
        self._ws = yield websocket.websocket_connect(self.url)
      except Exception as err: #pylint: disable=broad-except
        LOG.info("connection error")
        LOG.info(err)
        time.sleep(15)
      else:
        LOG.info("connected")
        connecting = False
        if argv:
          self.register(argv)
        self.run()

  @gen.coroutine
  def run(self):
    while True:
      msg = yield self._ws.read_message()
      if msg is not None:
        LOG.info("received message: " + str(msg))
        self.message_received(msg)
        self.ioloop.stop()
        break

def connect_portal(url, argv):
  global MESSAGE_RETURN #pylint: disable=global-statement

  Client(url, argv)
  LOG.info("FINISHED")
  return MESSAGE_RETURN

def client_ssm_thread(argv):

  url = 'ws://localhost:4001/ssm'
  if len(argv) < 1:
    LOG.error("Need to include a parameter ")
    sys.exit()

  #t = threading.Thread(target=connectPortal, args=(url,argv), daemon=True)
  #t.start()

  #t.join()
  return connect_portal(url, argv)
