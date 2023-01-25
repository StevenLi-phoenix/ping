import random
import select
# todo: why use select? No idea
import struct

import curio
from curio import spawn, timeout_after
import curio.socket as socket
import logging
import logging.handlers
import sys

from curio.debug import schedtrace
import c
import time
import os.path as osp
import os
import platform


# todo: 增加pygame作为UI 或者 自己写一个终端的UI
# todo: 确保 producer 大于一个


def file(filename):
    os.makedirs(osp.dirname(filename), exist_ok=True)
    return filename


def create_default_logger(stream=sys.stdout, name="", level=c.LEVEL, filename=f"log/{__name__}.log",
                          buffer=1024) -> logging.Logger:
    log = logging.getLogger(name)
    log.setLevel(level)
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s]: %(message)s')

    # set up logging to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)

    # set up logging to file
    file_handler = logging.FileHandler(filename=file(filename))
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    memoryhandler = logging.handlers.MemoryHandler(buffer, level, file_handler, flushOnClose=True)
    log.addHandler(memoryhandler)

    log.debug(platform.uname())

    return log


def do_checksum(source_string):
    print("Checksum")
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
    log.info("check sum complete -> %s" % answer)
    return answer


def test_log():
    log.critical("test")
    log.error("test")
    log.warning("test")
    log.info("test")
    log.debug("test")


log = create_default_logger(level=c.LEVEL, name="")
# todo: 使用模块中的 QueueHandler 和 QueueListener 对象logging将日志处理卸载到单独的线程
# 请注意，所有诊断日志记录都是同步的。因此，所有日志操作可能会暂时阻塞事件循环——尤其是当日志输
# 出涉及文件 I/O 或网络操作时。如果这是一个问题，您应该采取措施在日志记录配置中减轻它。例如，您
# 可以使用模块中的QueueHandler和 QueueListener对象logging将日志处理卸载到单独的线程
test_log()

# channel
# sended package hash map remain for consumer
hash_consumer = {}

sender_queue = curio.Queue()


class producer:
    Producer_ID = 0

    def __init__(self):
        producer.Producer_ID += 1
        self.ID = producer.Producer_ID
        self.socket = self.create_socket()
        self.working = False
        self.exitLock = False

        curio.run_in_thread(self.worker)

    async def send_package(self, hostname: str, ID: int, sock: socket.socket = None):
        """
        Send ping to target host
        :param sock: socket for sending ipv4_obj
        :param hostname: ipv4_obj address or hostname
        :param ID: UUID for host
        :return: Sender task instance
        """
        log.info("Send ICMP -- %s -> %s, worker: %s" % (sock, hostname, ID))
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

    async def worker(self):
        self.working = True
        while self.working:
            ipv4 = await sender_queue.get()
            ipv4addr, ID = ipv4.task()
            log.warning("Start working on %s@%s" % (ipv4addr, ID))
            await spawn(self.send_package, ipv4addr, ID)
            await sender_queue.task_done()
            ipv4.sent()
        log.info("Producer %s: terminated")
        self.exitLock = True

    def worker_terminate(self):
        self.working = False



class consumer:
    Consumer_ID = 0

    def __init__(self):
        consumer.Consumer_ID += 1
        self.ID = consumer.Consumer_ID
        self.working = False
        self.exitLock = False
        self.sock = self.create_socket()
        curio.run_in_thread(self.worker)

    def worker_terminate(self):
        self.working = False

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

    async def worker(self):
        self.working = True
        while self.working:
            recv_packet, addr = await self.sock.recvfrom(256)
            time_recieve = time.time()
            icmp_header = recv_packet[20:28]
            type, code, checksum, packet_ID, sequence = struct.unpack(
                "bbHHh", icmp_header
            )
            if packet_ID in hash_consumer.keys():
                bytes_In_double = struct.calcsize("d")
                time_sent = struct.unpack("d", recv_packet[28:28 + bytes_In_double])[0]
                ipv4 = hash_consumer[packet_ID]
                ipv4.recieved(time_recieve - time_sent)
                del hash_consumer[packet_ID]
        log.info("Consumer %s: terminated")
        self.exitLock = True


class ipv4_obj(object):
    ID = 0

    def __init__(self, ip1, ip2, ip3, ip4):
        self.ip = "%s.%s.%s.%s" % (ip1, ip2, ip3, ip4)
        self.ip1, self.ip2, self.ip3, self.ip4 = ip1, ip2, ip3, ip4
        ipv4_obj.ID += 1
        self.UUID = ipv4_obj.ID
        self.status = 0
        self.delay = 0
        self.condition = False
        log.info("[create]%s@%s" % (self.ip, self.UUID))
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
        log.info("[%s@%s] [requ]: %s -> 1" % (self.ip, self.UUID, self.status))
        self.status = 1
        return self.ip, self.UUID

    def sent(self):
        """
        update status to sent
        :return: None
        """
        log.info("[%s@%s] [sent] : %s -> 2" % (self.ip, self.UUID, self.status))
        self.status = 2

    def recieved(self, delay):
        log.info("[%s@%s] [recv]: %s -> 3" % (self.ip, self.UUID, self.status))
        self.delay = delay
        self.status = 3
        self.condition = True

    def no_response(self, retry=False):
        log.info("[%s@%s] [nors]: %s -> 3" % (self.ip, self.UUID, self.status))
        if retry:
            self.status = 4
        else:
            self.status = 5
            self.condition = True
            raise TimeoutError

    def condition_recieve(self):
        return self.condition


async def ipv4_order_line(ip1, ip2, ip3, ip4):
    cv = curio.Condition()
    ipv4 = ipv4_obj(ip1, ip2, ip3, ip4)
    await sender_queue.put(ipv4)
    hash_consumer[ipv4.UUID] = ipv4
    await cv.acquire()
    for i in range(c.RETRY_TIMES):
        try:
            await timeout_after(c.RETRY_TIMEOUT, cv.wait_for, ipv4.condition_recieve)
            return ipv4.delay
        except curio.TaskTimeout as e:
            log.error(f"TASK timeout(%ss) at {i} attempts" % e)
    await cv.release()


class ipv4_group256:
    async def init(self, ip1, ip2, ip3):
        self.task_list = [None for _ in range(256)]
        await self.create_task_group(ip1, ip2, ip3)

    async def create_task_group(self, ip1, ip2, ip3):
        async with curio.TaskGroup() as g:
            for i in range(0, 16):
                assert 0 <= i < 256
                t = await g.spawn(ipv4_order_line, ip1, ip2, ip3, i)
                self.task_list[i] = t
        print('Results:', g.results)


class worker_manager:
    working_flag = True

    async def create_pool(self, size=16):
        cv = curio.Condition()
        while worker_manager.working_flag:
            producer_count = size // 2
            consumer_count = size - producer_count
            producer_list = [producer() for i in range(producer_count)]
            consumer_list = [consumer() for i in range(consumer_count)]
            await curio.sleep(2)
            await cv.acquire()
            if len(hash_consumer) > 0:
                t = random.choice(producer_list)
                t.worker_terminate()
                await cv.wait_for(t.exitLock)
                consumer_list.append(consumer())
            else:
                t = random.choice(consumer_list)
                t.worker_terminate()
                await cv.wait_for(t.exitLock)
                producer_list.append(producer())
            await cv.release()
        log.info("Worker pool exit")
        return time.time()


worker = worker_manager()

def worker_terminate():
    worker.working_flag = False

async def worker_start(size=16):
    await worker.create_pool(size)

async def main():

    await worker_start()
    await ipv4_group256().init(192, 168, 1)


if __name__ == '__main__':
    # for ip in tqdm(range(256*256*256)):
    # 172.20.10.*
    curio.run(main)
    # ipv4_group1 = ipv4_group256(172, 20, 10)
