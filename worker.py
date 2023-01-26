import logging
import struct
import time

import curio
from curio import socket

import c


class worker(object):
    workerID = 0  # global ID
    hash_consumer = {}
    sender_queue = curio.Queue()

    def __init__(self, name="default"):
        worker.workerID += 1
        self.name = name
        self.ID = worker.workerID
        self.sock = self.create_socket()
        self.log = logging.getLogger("worker.%s" % self.ID)
        self.working = False
        self.exitLock = False

    async def init(self):
        self.log.info("Worker %s start" % self.ID)
        await curio.run_in_thread(self.worker, call_on_cancel=self.terminate)
        self.log.info("Worker %s terminated" % self.ID)

    def do_checksum(self, source_string):
        print("Checksum")
        """  Verify the packet integritity """
        self.log.info("calculate %s checksum" % source_string)
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
        self.log.info("check sum complete -> %s" % answer)
        return answer

    async def worker(self):
        # Override this function
        self.working = True
        while self.working:
            await curio.sleep(1)
        self.exitLock = True

    def terminate(self):
        self.working = False

    def getExitLock(self):
        return self.exitLock

    def create_socket(self) -> socket.socket:
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

    def close_socket(self):
        self.sock.close()


class producer(worker):
    def __init__(self):
        super().__init__()
        self.log.debug("Producer")

    async def send_package(self, hostname: str, ID: int, sock: socket.socket = None):
        """
        Send ping to target host
        :param sock: socket for sending ipv4_obj
        :param hostname: ipv4_obj address or hostname
        :param ID: UUID for host
        :return: Sender task instance
        """
        self.log.info("Send ICMP -- %s -> %s, worker: %s" % (sock, hostname, ID))
        if sock is None:
            sock = self.sock

        target_addr = await socket.gethostbyname(hostname)

        # dummy checksum
        my_checksum = 0
        # Create a dummy heder with a 0 checksum.
        header = struct.pack("bbHHh", c.ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
        bytes_In_double = struct.calcsize("d")
        data = (192 - bytes_In_double) * "Q"
        data = struct.pack("d", time.time()) + bytes(data.encode('utf-8'))

        # Get the checksum on the data and the dummy header.
        my_checksum = self.do_checksum(header + data)
        header = struct.pack(
            "bbHHh", c.ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1
        )
        packet = header + data

        t = await curio.spawn(sock.sendto, packet, (target_addr, 1))
        return t

    async def worker(self):
        self.working = True
        while self.working:
            ipv4 = await worker.sender_queue.get()
            ipv4addr, ID = ipv4.task()
            self.log.info("Start working on %s@%s" % (ipv4addr, ID))
            await curio.spawn(self.send_package, ipv4addr, ID)
            await worker.sender_queue.task_done()
            ipv4.sent()
        self.exitLock = True


class consumer(worker):
    def __init__(self):
        super().__init__()
        self.log.info("Consumer")

    async def worker(self):
        self.working = True
        while self.working:
            recv_packet, addr = await self.sock.recvfrom(256)
            time_recieve = time.time()
            icmp_header = recv_packet[20:28]
            type, code, checksum, packet_ID, sequence = struct.unpack(
                "bbHHh", icmp_header
            )
            if packet_ID in worker.hash_consumer.keys():
                bytes_In_double = struct.calcsize("d")
                time_sent = struct.unpack("d", recv_packet[28:28 + bytes_In_double])[0]
                ipv4 = worker.hash_consumer[packet_ID]
                ipv4.recieved(time_recieve - time_sent)
                del worker.hash_consumer[packet_ID]
        self.log.info("Consumer %s: terminated")
        self.exitLock = True




# class producer:
#     Producer_ID = 0
#
#     def __init__(self):
#         producer.Producer_ID += 1
#         self.ID = producer.Producer_ID
#         self.socket = self.create_socket()
#         self.working = False
#         self.exitLock = False
#
#     async def init(self):
#         await curio.run_in_thread(self.worker, call_on_cancel=self.worker_terminate)
#         return self
#
#     async def send_package(self, hostname: str, ID: int, sock: socket.socket = None):
#         """
#         Send ping to target host
#         :param sock: socket for sending ipv4_obj
#         :param hostname: ipv4_obj address or hostname
#         :param ID: UUID for host
#         :return: Sender task instance
#         """
#         log.info("Send ICMP -- %s -> %s, worker: %s" % (sock, hostname, ID))
#         if sock is None:
#             sock = self.socket
#
#         target_addr = await socket.gethostbyname(hostname)
#
#         # dummy checksum
#         my_checksum = 0
#         # Create a dummy heder with a 0 checksum.
#         header = struct.pack("bbHHh", c.ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
#         bytes_In_double = struct.calcsize("d")
#         data = (192 - bytes_In_double) * "Q"
#         data = struct.pack("d", time.time()) + bytes(data.encode('utf-8'))
#
#         # Get the checksum on the data and the dummy header.
#         my_checksum = do_checksum(header + data)
#         header = struct.pack(
#             "bbHHh", c.ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1
#         )
#         packet = header + data
#
#         t = await spawn(sock.sendto, packet, (target_addr, 1))
#         return t
#
#     def create_socket(self) -> socket.socket:
#         """
#         create a socket
#         :param ID: threadID
#         :return: socket
#         """
#         icmp = socket.getprotobyname("icmp")
#         try:
#             sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
#             return sock
#         except socket.error as e:
#             if e.errno == 1:
#                 # root privilliage needed
#                 e.msg += "ICMP messages can only be sent from root user processes"
#                 raise socket.error(e.msg)
#         except Exception as e:
#             print("Exception: %s" % e)
#
#     async def worker(self):
#         self.working = True
#         while self.working:
#             ipv4 = await sender_queue.get()
#             ipv4addr, ID = ipv4.task()
#             log.warning("Start working on %s@%s" % (ipv4addr, ID))
#             await spawn(self.send_package, ipv4addr, ID)
#             await sender_queue.task_done()
#             ipv4.sent()
#         log.info("Producer %s: terminated")
#         self.exitLock = True
#
#     def worker_terminate(self):
#         self.working = False
#
#     def getExitLock(self):
#         return self.exitLock


# class consumer:
#     Consumer_ID = 0
#
#     def __init__(self):
#         consumer.Consumer_ID += 1
#         self.ID = consumer.Consumer_ID
#         self.working = False
#         self.exitLock = False
#         self.sock = self.create_socket()
#
#     async def init(self):
#         await curio.run_in_thread(self.worker, call_on_cancel=self.worker_terminate)
#         return self
#
#     def worker_terminate(self):
#         self.working = False
#
#     def create_socket(self) -> socket.socket:
#         """
#         create a socket
#         :param ID: threadID
#         :return: socket
#         """
#         icmp = socket.getprotobyname("icmp")
#         try:
#             sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
#             return sock
#         except socket.error as e:
#             if e.errno == 1:
#                 # root privilliage needed
#                 e.msg += "ICMP messages can only be sent from root user processes"
#                 raise socket.error(e.msg)
#         except Exception as e:
#             print("Exception: %s" % e)
#
#     async def worker(self):
#         self.working = True
#         while self.working:
#             recv_packet, addr = await self.sock.recvfrom(256)
#             time_recieve = time.time()
#             icmp_header = recv_packet[20:28]
#             type, code, checksum, packet_ID, sequence = struct.unpack(
#                 "bbHHh", icmp_header
#             )
#             if packet_ID in hash_consumer.keys():
#                 bytes_In_double = struct.calcsize("d")
#                 time_sent = struct.unpack("d", recv_packet[28:28 + bytes_In_double])[0]
#                 ipv4 = hash_consumer[packet_ID]
#                 ipv4.recieved(time_recieve - time_sent)
#                 del hash_consumer[packet_ID]
#         log.info("Consumer %s: terminated")
#         self.exitLock = True
#
#     def getExitLock(self):
#         return self.exitLock
