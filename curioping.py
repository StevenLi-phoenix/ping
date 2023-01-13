import atexit
import os
import queue
import struct
import select
import sys
import time
import logging

# 异步进程部分需要
# todo: 研究这些包都是用来干什么的？
import uuid

from curio import run, spawn
from curio.socket import *
import curio

# ICMP package Type 8 -- Echo: A a query a host sends to see if a potential destination system is available. Upon receiving an Echo message, the receiving device might send back an Echo Reply
ICMP_ECHO_REQUEST = 8  # Platform specific

DEFAULT_TIMEOUT = 2
DEFAULT_COUNT = 10


def creat_log(filename=f"{__name__}.log", level=logging.DEBUG, stream=sys.stdout):
    log = logging.getLogger('')
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s]: %(message)s')

    # set up logging to console
    console_handler = logging.StreamHandler(stream=stream)
    console_handler.setLevel(level=level)
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)

    # set up logging to file
    file_handler = logging.FileHandler(filename=filename)
    file_handler.setLevel(level=level)
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

    return log

# create logging
log = creat_log()

listener_queue = queue.SimpleQueue()


# It has nothing to do with class ping_sender, thus it's a global method
def do_checksum(source_string):
    """  Verify the packet integritity """
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
    return answer


class ping_sender(object):
    """ Pings a host """

    def __init__(self, count=DEFAULT_COUNT, timeout=DEFAULT_TIMEOUT):
        self.count = count
        self.timeout = timeout

    async def send_ping(self, sock: socket, socket_ID: int, target_host: str) -> None:
        """
        Send Ping package
        :param sock: socket.socket for TCP connection
        :param socket_ID: int for identify, should be globally self-increment
        :param target_host: target host IP address
        :return: int, delay
        """
        target_addr = gethostbyname(target_host)
        package_checksum = 0

        # create a dummy header with 0 checksum
        header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, package_checksum, socket_ID, 1)

        bytes_in_double = struct.calcsize("d")
        data = (
                       192 - bytes_in_double) * "Q"  # todo: check if this could change to meaning content like timestamp or stuff
        data = struct.pack("d", time.time()) + bytes(data.encode("utf-8"))

        # get checksum on the header and summy header
        package_checksum = do_checksum(header + data)
        header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, htons(package_checksum), socket_ID, 1)
        package = header + data

        # send package by socket
        await sock.sendto(package, (target_addr, 1))

        # send package info to listener_queue
        listener_queue.put(socket_ID)


class worker:
    UUID = 0

    def __init__(self):
        worker.UUID += 1
        self.worker_ID = worker.UUID
        self.target_id = 0  # 0 for idle and ip for waiting ip
        self.sock = self.create_socket()
        atexit.register(self.close_socket)
        log.warning("socket created")  # temp

    async def close_socket(self):
        log.debug("socket close")

        await self.sock.close()

    def create_socket(self):
        icmp = getprotobyname("icmp")
        try:
            sock = socket(AF_INET, SOCK_RAW, icmp)
        except error as e:
            if e.errno == 1:
                # Not superuser, so operation not permitted
                e.msg += "ICMP messages can only be sent from root user processes"
                raise error(e.msg)
        except Exception as e:
            print("Exception: %s" % (e))
        return sock

    def listening(self):
        self.target_id = listener_queue.get()

    # todo: 将这部分从class中移除，然后专门建立一个用于receieve的class
    async def receieve_pong(self, sock: socket, ID: int, timeout: int) -> int:
        """
        Receieve pong from replay package
        :param sock: socket.socket for TCP connection
        :param ID: int for identify, should be globally self-increment
        :param timeout: second for timeout
        :return: delay in ms, 0 if failed
        """
        delay = 0
        time_remaining = timeout
        while True:
            start_time = time.time()
            readable = select.select([sock], [], [], time_remaining)
            time_spent = (time.time() - start_time)
            if readable[0] == []:  # Timeout
                return 0  # failed

            recv_packet, addr = await sock.recvfrom(1024)

            time_received = time.time()
            icmp_header = recv_packet[20:28]
            type, code, checksum, packet_ID, sequence = struct.unpack(
                "bbHHh", icmp_header
            )

            # todo: 这种方法在高并发的情况下会崩溃
            if packet_ID == ID:  # wtf is this
                bytes_In_double = struct.calcsize("d")
                time_sent = struct.unpack("d", recv_packet[28:28 + bytes_In_double])[0]
                return time_received - time_sent

            time_remaining = time_remaining - time_spent
            if time_remaining <= 0:
                return 0

async def main():
    obj = worker()
    await obj.close_socket()


if __name__ == '__main__':
    run(main(), with_monitor=True)
