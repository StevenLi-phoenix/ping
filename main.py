import logging
import socket
import queue
import struct
import threading
import time
import os.path as osp

import CONFIG
import logger
import task_client

log = logger.create_default_logger()


class worker:
    GLOBAL_ID = 0
    IPV4_256_block = {i: False for i in range(65536)}
    task = 0

    def __init__(self):
        self.id = worker.GLOBAL_ID
        worker.GLOBAL_ID += 1
        self.log = logging.getLogger("worker")
        self.log.debug(f"Worker {self.id} started")
        self.sock = self.create_socket()
        self.working = True

    @staticmethod
    def reset_IPV4_256_block():
        worker.IPV4_256_block = {i: False for i in range(65536)}

    def do_checksum(self, source_string):
        """  Verify the packet integrity """
        self.log.debug("calculate %s checksum" % source_string)
        sums = 0
        max_count = (len(source_string) / 2) * 2
        count = 0
        while count < max_count:
            val = source_string[count + 1] * 256 + source_string[count]
            sums = sums + val
            sums = sums & 0xffffffff
            count = count + 2

        if max_count < len(source_string):
            sums = sums + ord(source_string[len(source_string) - 1])
            sums = sums & 0xffffffff

        sums = (sums >> 16) + (sums & 0xffff)
        sums = sums + (sums >> 16)
        answer = ~sums
        answer = answer & 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)
        self.log.debug("check sum complete -> %s" % answer)
        return answer

    def create_socket(self) -> socket.socket:
        """
        create a socket
        :return: socket
        """
        self.log.debug("Create Socket")
        icmp = socket.getprotobyname("icmp")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
            return sock
        except socket.error as e:
            if e.errno == 1:
                # root privilege needed
                # e.msg += "ICMP messages can only be sent from root user processes"
                raise socket.error(e)
        except Exception as e:
            self.log.error("Exception: %s" % e)

    def close_socket(self):
        self.sock.close()

    def IPV4_to_ID(self, hostname) -> int:
        ip1, ip2, ip3, ip4 = hostname.split(".")
        return int(ip1) * 256 ** 3 + int(ip2) * 256 ** 2 + int(ip3) * 256 ** 1 + int(ip4)

    def ID_to_IPV4(self, IPV4ID) -> str:
        return str(IPV4ID // 256 ** 3 % 256) + "." + str(IPV4ID // 256 ** 2 % 256) + "." + str(
            IPV4ID // 256 ** 1 % 256) + "." + str(IPV4ID % 256)

    def IPV4_to_BlockID(self, hostname) -> int:
        return int(hostname.split(".")[3])

    def packageID_to_BlockID(self, packageID: int) -> int:
        return packageID % 256


class sender(worker):
    sender_queue = queue.SimpleQueue()

    def __init__(self):
        super().__init__()
        self.log = logging.getLogger("sender")

    def send_package(self, hostname: str, ID: int = None, sock: socket.socket = None,
                     retries=c.RETRY_TIMES):
        if sock is None:
            sock = self.sock
        if ID is None:
            ID = self.IPV4_to_ID(hostname) % 65536
        if ID % 256 == 0:
            self.log.info(f"Sending ICMP on {hostname}/8")
        self.log.debug("Send ICMP -- %s -> %s, worker: %s" % (sock, hostname, self.id))
        # dummy checksum
        my_checksum = 0
        # Create a dummy header with a 0 checksum.
        header = struct.pack("bbHHh", c.ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
        data = ""
        data = struct.pack("d", time.time()) + bytes(data.encode('utf-8'))

        # Get the checksum on the data and the dummy header.
        my_checksum = self.do_checksum(header + data)
        header = struct.pack(
            "bbHHh", c.ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1
        )
        packet = header + data
        self.log.debug(f"Start sendto {hostname} with {packet}")
        try:
            sock.sendto(packet, (hostname, 1))
        except OSError as e:
            if retries > 0:
                self.send_package(hostname=hostname, ID=ID, sock=sock, retries=retries - 1)
            else:
                log.debug(e)

    def thread(self):
        self.log.info(f"{self.id}: start thread")
        while self.working:
            ipv4Addr = self.sender_queue.get()
            self.log.debug(f"{self.id} Start working on {ipv4Addr}")
            self.send_package(ipv4Addr)
            self.log.debug(f"Delay on {ipv4Addr}")


class receiver(worker):
    def __init__(self):
        super().__init__()

    def receive_package(self):
        recv_packet, addr = self.sock.recvfrom(256)
        icmp_header = recv_packet[20:28]
        _, _, _, packet_ID, _ = struct.unpack("bbHHh", icmp_header)
        if packet_ID in worker.IPV4_256_block.keys():
            log.info(f"received package from {self.ID_to_IPV4(packet_ID + worker.task * 65535)} with receiver{self.id}")
            worker.IPV4_256_block[packet_ID] = True

    def thread(self):
        self.log.info("Consumer %s: start" % self.id)
        while self.working:
            self.receive_package()
        self.log.info("Consumer %s: terminated" % self.id)


def main(ip):
    ip1, ip2 = ip // 256, ip % 256
    worker.task = ip
    log.info(f"Start group {ip1}-{ip2}")
    for ip3 in range(256):
        for i in range(256):
            sender.sender_queue.put(f"{ip1}.{ip2}.{ip3}.{i}")
        time.sleep(0.1)
    while not sender.sender_queue.empty():
        time.sleep(1)
    time.sleep(2)
    assert len(worker.IPV4_256_block) == 65536
    s = ""
    for i in range(65535):
        if worker.IPV4_256_block[i]:
            s += "1"
        else:
            s += "0"
    with open(logger.file(osp.join("ip", str(ip1), str(ip2))), "w+") as f:
        f.write(s)
    worker.reset_IPV4_256_block()
    return s


# server_url = "http://172.16.82.60:8001"
server_url = "http://47.95.223.74:8001"
# server_url = "http://127.0.0.1:8001"

if __name__ == '__main__':
    threading.Thread(target=sender().thread).start()
    threading.Thread(target=receiver().thread).start()
    while True:
        task = task_client.get_task(server_url)
        result = main(task)
        task_client.submit_task(server_url, task, result)
