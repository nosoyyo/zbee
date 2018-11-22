import os
import zmq
import json
import time
import redis
from wxpy import Bot, ensure_one

from hbee import HealthBee
from mail import mailQRCode
from utils.sigmaactions import sigmaActions
from utils.safecheck import slowDown, safeCheck


class WXBeeError(Exception):
    pass


class WXBee():

    hbee = HealthBee('wxbee')

    cpool = redis.ConnectionPool(host='localhost', port=6379,
                                 decode_responses=True, db=5)
    r = redis.Redis(connection_pool=cpool)

    context = zmq.Context()
    sink = context.socket(zmq.PULL)
    sink.bind('tcp://192.168.1.112:5558')

    def __init__(self):
        self.bee = Bot(logout_callback=self.tryRestart)
        self.dest = ensure_one(self.bee.search('msfc'))
        print('WXBee initiating...')
        print(f'dest: {self.dest}')
        while True:
            print('start receiving data...')
            data = self.sink.recv()
            self.send(data)

        @self.bee.register(chats=None,
                           msg_types=None,
                           except_self=False,
                           run_async=True,
                           enabled=True)
        def handler(msg):
            print('WXBee.handler functioning')
            if 'checkServiceStatus' in msg:
                self.hbee.healthCheck()
            while True:
                print('start receiving data...')
                data = self.sink.recv()
                self.send(data)

    def __del__(self):
        self.context.term()

    def tryRestart(self):
        self.bee = Bot(qr_callback=mailQRCode)

    @safeCheck
    @slowDown
    def _SEND(self, _str):
        try:
            self.dest.send(_str)
        except Exception as e:
            print(e)
            raise WXBeeError(e)
        finally:
            sigmaActions(self.r, time.time())

    @safeCheck
    @slowDown
    def _SEND_VIDEO(self, _video):
        if isinstance(_video, str) and os.path.isfile(_video):
            print(f'sending {_video}...')
        else:
            raise WXBeeError('only accept absolute file path!')

        try:
            self.dest.send_video(_video)
        except Exception as e:
            print(e)
            raise WXBeeError(e)
        finally:
            sigmaActions(self.r, time.time())

    def send(self, data):
        self.dataHandler(data)

    def dataHandler(self, data: bytes):
        '''
        :param data: <>
        '''

        try:
            j = json.loads(data)
        except json.decoder.JSONDecodeError:
            data = data.decode()
            if '\\U' in data:
                data = '{"string": "emoji is not supported!"}'.encode()
            elif "'" in data:
                data = data.replace("'", '"').encode()
            j = json.loads(data)
        except Exception as e:
            raise WXBeeError(e)
        key = ensure_one([k for k in j])

        if key == 'string':
            self._SEND(j[key])
        elif key == 'video':
            self._SEND_VIDEO(j[key])
        else:
            raise NotImplementedError


def main():
    WXBee()


if __name__ == "__main__":
    main()
