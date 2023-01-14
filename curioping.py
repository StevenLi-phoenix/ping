import struct

import curio
from curio import spawn, timeout_after
import curio.socket as socket
import logging
import sys
import c
import time
import os.path as osp
import os
import platform


def file(filename):
    os.makedirs(osp.dirname(filename), exist_ok=True)
    return filename


def create_logger(stream=sys.stdout, level=logging.INFO, filename=f"log/{__name__}.log") -> logging.Logger:
    log = logging.getLogger("")
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s]: %(message)s')

    # set up logging to console
    console_handler = logging.StreamHandler(stream=stream)
    console_handler.setLevel(level=level)
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)

    # set up logging to file
    file_handler = logging.FileHandler(filename=file(filename))
    file_handler.setLevel(level=level)
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

    log.debug(platform.uname())

    return log


def do_checksum(source_string):
    """  Verify the packet integritity """
    log.info("calculate %s checksum" % source_string)
    sum = 0
    max_count = (len(source_string) / 2) * 2
    count = 0
    while count < max_count:
        val = source_string[count + 1] * 256 + source_string[count]
        sum = sum + val
        sum = sum & 0xffffffff
        count = count + 2

    if max_count < len(source_string):
        sum = sum + ord(source_string[len(source_string) - 1])
        sum = sum & 0xffffffff

    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    log.debug("check sum complete -> %s" % answer)
    return answer


log = create_logger(level=c.LEVEL, filename=osp.join(c.LogDirectionary, "%s.log" % __name__))

# channel
# sended package hash map remain for consumer
hash_consumer = {}

sender_queue = curio.Queue()

class producer:
    Producer_ID = 0
    def __init__(self):
        producer.Producer_ID += 1
        self.ID = producer.Producer_ID
        self.socket = self.create_socket(self.ID)
        self.working = False


        curio.run_in_thread(self.worker)

    async def send_package(self, hostname:str, ID:int, sock:socket.socket=None):
        """
        Send ping to target host
        :param sock: socket for sending ipv4
        :param hostname: ipv4 address or hostname
        :param ID: UUID for host
        :return: Sender task instance
        """
        log.debug("Send ICMP -- %s -> %s, worker: %s" % (sock, hostname, ID))
        if sock is None:
            sock = self.socket

        target_addr = await socket.gethostbyname(hostname)

        # dummy checksum
        my_checksum = 0
        # Create a dummy heder with a 0 checksum.
        header = struct.pack("bbHHh", c.ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
        bytes_In_double = struct.calcsize("d")
        data = (192 - bytes_In_double) * "Q"
        data = struct.pack("d", time.time()) + bytes(data.encode('utf-8'))

        # Get the checksum on the data and the dummy header.
        my_checksum = do_checksum(header + data)
        header = struct.pack(
            "bbHHh", c.ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1
        )
        packet = header + data

        t = await spawn(sock.sendto, packet, (target_addr, 1))
        return t

    async def create_socket(self, ID) -> socket.socket:
        """
        create a socket
        :param ID: threadID
        :return: socket
        """
        icmp = socket.getprotobyname("icmp")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
            return sock
        except socket.error as e:
            if e.errno == 1:
                # root privilliage needed
                e.msg += "ICMP messages can only be sent from root user processes"
                raise socket.error(e.msg)
        except Exception as e:
            print("Exception: %s" % e)

    async def worker(self):
        self.working = True
        while self.working:
            ipv4 = await sender_queue.get()
            ipv4addr, ID = ipv4.task()
            hash_consumer[ID] = await spawn(self.send_package, ipv4addr, ID)
            await sender_queue.task_done()


    def worker_terminate(self):
        self.working = False

class ipv4(object):
    ID = 0
    def __init__(self, ip1, ip2, ip3, ip4):
        self.ip = "%s.%s.%s.%s" % (ip1, ip2, ip3, ip4)
        self.ip1, self.ip2, self.ip3, self.ip4 = ip1, ip2, ip3, ip4
        ipv4.ID += 1
        self.ID = ipv4.ID
        self.status = 0
        """
        -1: force quit due to uncaught exception or similar
        0: prepare
        1: be requested
        2: sent and put in reciever queue
        3: recieved
        4: No response and retrying
        5. No response after timeout
        """

    def task(self): 
        self.status = 1
        return self.ip, self.ID
    def sent(self):
        """
        update status to sent
        :return: None
        """
        self.status = 2
        spawn(timeout_after(2, coro=None))




def order():
    pass


class ipv4_group256:
    def __init__(self):
        self.task_list = [None for _ in range(256)]
    async def create_task_group(self, ip1, ip2, ip3):
        async with curio.TaskGroup() as g:
            for i in range(256):
                t = await g.spawn()
                self.task_list[i] = t
                print(t.id)


if __name__ == '__main__':
    p = producer()
    curio.run(p.send_package(hostname="47.95.223.74",ID=0,sock=socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))))

