import os
import zmq
import redis

from hbee import HealthBee


class ZBeeError(Exception):
    pass


class ZBee():

    '''
    bytes in bytes out.
    '''
    hbee = HealthBee('zbee')

    cpool = redis.ConnectionPool(host='localhost', port=6379,
                                 decode_responses=True, db=5)
    r = redis.Redis(connection_pool=cpool)

    context = zmq.Context()
    pipe_receiver = context.socket(zmq.PULL)
    pipe_receiver.bind('tcp://192.168.1.112:5557')
    semi = context.socket(zmq.PUSH)
    semi.connect('tcp://192.168.1.112:5558')

    def __init__(self):
        while True:
            data = self.pipe_receiver.recv()
            data = data.decode()
            if 'checkServiceStatus' in data:
                self.hbee.healthCheck()
            else:
                print(f'received from 5557: {data}')
                self.handle(data)

    def __del__(self):
        self.context.term()

    def handle(self, data):
        data = self.unpackage(data)
        parsed = self.parse(data)
        payload = self.package(parsed)
        self.deliver(payload)

    def unpackage(self, data):
        if isinstance(data, bytes):
            data = data.decode()
        return data

    def parse(self, data):
        return data

    def package(self, data):

        if os.path.isfile(data):
            if data.split('.')[-1] == 'mp4':
                data = {"video": data}
            else:
                raise ZBeeError('only support mp4 now.')
        else:
            data = {"string": data}

        return data.__str__().replace("'", '"').encode()

    def deliver(self, dealt_data):
        flag = False
        try:
            self.semi.send(dealt_data)
            print(f'sent to 5558: {dealt_data}')
        except Exception as e:
            print(e)
            flag = False
        return flag


def main():

    try:
        ZBee()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
