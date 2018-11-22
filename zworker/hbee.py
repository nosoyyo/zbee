import os
import zmq
import time
import redis
import psutil
import schedule

from utils.tiempo import fancyTQ, fancyTiempo


class HealthBee():
    cpool = redis.ConnectionPool(host='localhost', port=6379,
                                 decode_responses=True, db=5)
    r = redis.Redis(connection_pool=cpool)

    context = zmq.Context()
    pipe_sender = context.socket(zmq.PUSH)
    pipe_sender.connect('tcp://192.168.1.112:5557')

    def __init__(self, hostname: str):
        '''
        :param hostname: <str> used as hashkey of hset(hostname, pid)
        '''
        self.hostname = hostname
        pid = self.r.hkeys(hostname) or None
        print(f'{hostname} pid before init: {pid}')
        if pid:
            keys = self.r.hkeys(hostname)
            for key in keys:
                self.r.hdel(hostname, key)
            print(f'{len(keys)} previous pids cleared.')
        pid = os.getpid()
        self.r.hset(hostname, pid, time.time())
        self.PID = pid
        print(f'{hostname} pid after init: {pid}')

        schedule.every(30).minutes.do(self.healthCheck)
        print(schedule.jobs[0])

    def __del__(self):
        if self.PID and self.hostname:
            self.r.hdel(self.hostname, self.PID)
        schedule.clear()

    def healthCheck(self, hostname=None):

        flag = False
        hostname = hostname or self.hostname
        now = time.time()
        info = f'checking {hostname} on {fancyTiempo()}... '
        pid = int(self.r.hkeys(hostname)[0]) or None
        print(f'get {hostname} pid: {pid}')
        pids = psutil.pids()
        if pid:
            if pid in pids:
                t = self.r.hget(hostname, pid)
                if t:
                    q = now - float(t)
                    info += f"{hostname} has been working for {fancyTQ(q)}"
                    flag = True
        else:
            info += 'HealthBee got no PID! must be something wrong!'

        print(info)
        self.pipe_sender.send(info.encode())
        return flag
