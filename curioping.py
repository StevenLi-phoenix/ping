import random

from curio import timeout_after

from worker import *
from logger import *

# todo: 增加pygame作为UI 或者 自己写一个终端的UI
# todo: 确保 producer 大于一个


log = create_default_logger(level=c.LEVEL, name="")


# todo: 使用模块中的 QueueHandler 和 QueueListener 对象logging将日志处理卸载到单独的线程
# 请注意，所有诊断日志记录都是同步的。因此，所有日志操作可能会暂时阻塞事件循环——尤其是当日志输
# 出涉及文件 I/O 或网络操作时。如果这是一个问题，您应该采取措施在日志记录配置中减轻它。例如，您
# 可以使用模块中的QueueHandler和 QueueListener对象logging将日志处理卸载到单独的线程

# channel
# sended package hash map remain for consumer

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
    await worker.sender_queue.put(ipv4)
    worker.hash_consumer[ipv4.UUID] = ipv4
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
            producer_list = [producer() for _ in range(producer_count)]
            consumer_list = [consumer() for _ in range(consumer_count)]
            for p in producer_list:
                await p.init()
            for c in consumer_list:
                await c.init()
            await curio.sleep(2)
            worker_manager.working_flag = False
            continue
            await cv.acquire()
            if len(hash_consumer) > 0:
                log.info(
                    f"Add consumer, producer:{len(producer_list)} -> {len(producer_list) - 1}, consumer:{len(consumer_list)} -> {len(consumer_list) + 1}")
                t = random.choice(producer_list)
                t.worker_terminate()
                await cv.wait_for(t.getExitLock)
                consumer_list.append(consumer())
            else:
                log.info(
                    f"Add consumer, producer:{len(producer_list)} -> {len(producer_list) + 1}, consumer:{len(consumer_list)} -> {len(consumer_list) - 1}")
                t = random.choice(consumer_list)
                t.worker_terminate()
                await cv.wait_for(t.getExitLock)
                producer_list.append(producer())
            await cv.release()
        log.info("Worker pool exit")
        return time.time()


worker = worker_manager()


def worker_terminate():
    worker.working_flag = False


async def worker_start(size=16):
    await worker.create_pool(size)


async def main_start():
    await worker_start()
    await ipv4_group256().init(192, 168, 1)


def main():
    curio.run(main_start)


if __name__ == '__main__':
    # for ip in tqdm(range(256*256*256)):
    # 172.20.10.*
    main()
    # ipv4_group1 = ipv4_group256(172, 20, 10)
