import threading
import queue
from time import sleep


# ---- multi threading ----
worker = 256
# ---- IMCP ----
ICMP_ECHO_REQUEST = 8  # Platform specific
DEFAULT_TIMEOUT = 2
DEFAULT_COUNT = 10
# ---- queue ----
sender_queue = queue.Queue()
receiver_queue = queue.Queue()


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


class pingblock_256:
    def __init__(self, ip1, ip2, ip3):
        self.queue = queue.Queue()
        self.ip = "%s.%s.%s.0/24" % (ip1, ip2, ip3)
        self.ip_list = []
        for i in range(256):
            self.ip_list.append(ip_block(ip1, ip2, ip3, i))

    def sendpackages(self):
        for i in self.ip_list:
            sender_queue.put(i)

    def checkResponse(self):
        def thread_checkResponse():
            while not all(i.ping for i in self.ip_list):
                sleep(1)
            return True
        t = threading.Thread(target=thread_checkResponse)
        t.start()
        t.join()
        print("finish")
        # ignoretodo dump json to file by ip1, ip2, ip3 and self.ip_list








class Pinger(object):
    def __init__(self, count=DEFAULT_COUNT, timeout=DEFAULT_TIMEOUT, worker_count=worker):
        self.count = count
        self.timeout = timeout
        self.worker_count = worker_count


class ip_block(object):
    UUID = 0 # self-increment

    def __init__(self, ip1, ip2, ip3, ip4):
        self.ip = "%s.%s.%s.%s" % (ip1, ip2, ip3, ip4)
        self.ip1 = ip1
        self.ip2 = ip2
        self.ip3 = ip3
        self.ip4 = ip4
        ip_block.UUID += 1
        self.id = ip_block.UUID # self-increment
        self.delay = 0
        self.status = False # True for online, False for offline
        self.ping = False # True if sent ICMP package

    def status(self):
        return self.ping

    def getIP(self):
        return self.ip


if __name__ == '__main__':
    pass
