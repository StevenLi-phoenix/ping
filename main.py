import json
from time import sleep
import os
import os.path as osp

import ping
# import multiprocess
import threading
import queue

Global_ID = 0
# q = queue.Queue()
q_w = queue.Queue()
queue_list = queue.Queue()
FLAG_q_alltaskdone = False

q_w.not_empty

def worker():
    global Global_ID
    while True:
        queue_subpart = queue_list.get()
        while queue_subpart.not_empty:
            item = queue_subpart.get()
            Global_ID += 1
            ID = Global_ID
            ip1, ip2, ip3, ip4 = item
            delay = ping.Pinger(target_host=".".join([str(i) for i in item])).ping_any(ID)
            all_ipv4[ip1][ip2][ip3][ip4] = delay
            queue_subpart.task_done()
        write_hash(queue_subpart.ipv4, queue_subpart.filename)
        queue_list.task_done()

# def writing():
#     while True:
#         if not q_w.empty() or FLAG_q_alltaskdone:
#             hashd, filename = q_w.get()
#             write_hash(hashd, filename)
#             q_w.task_done()
#             # q_w.unfinished_tasks()
#         else:
#             sleep(1)

def write_hash(hash, filename):
    os.makedirs(osp.dirname(osp.abspath(filename)), exist_ok=True)
    json.dump(hash, open(filename, "w"))
    print("_________________________ write: %s _________________________"%filename)


tn = 4
ts = [threading.Thread(target=worker, daemon=True).start() for i in range(tn)]
# tw = threading.Thread(target=writing, daemon=True).start()


ipv1_low, ipv1_up = 47, 48
ipv2_low, ipv2_up = 95, 96
ipv3_range = 256
ipv4_range= 256

all_ipv4 = {}
for ip1 in range(ipv1_low, ipv1_up):
    if ip1 not in all_ipv4.keys(): all_ipv4[ip1] = {}
    for ip2 in range(ipv2_low, ipv2_up):
        if ip2 not in all_ipv4[ip1].keys(): all_ipv4[ip1][ip2] = {}
        for ip3 in range(256):
            if ip3 not in all_ipv4[ip1][ip2].keys(): all_ipv4[ip1][ip2][ip3] = {}
            q_subset = queue.Queue()
            q_subset.ipv4 = all_ipv4[ip1][ip2][ip3]
            q_subset.filename = osp.join(str(ip1), str(ip2), str(ip3) + ".json")
            queue_list.put(q_subset) # keep track of queue
            for ip4 in range(256):
                # create a new queue
                # if ip4 not in all_ipv4[ip1][ip2][ip3].keys(): all_ipv4[ip1][ip2][ip3][ip4] = 0
                q_subset.put((ip1, ip2, ip3, ip4))
                # load task to sub-queue
            # q.join()
            # q_w.put((all_ipv4[ip1][ip2][ip3], osp.join(str(ip1), str(ip2), str(ip3) + ".json")))
        # print(ip1, ip2)


while any(not q_i.empty() for q_i in queue_list):
    for q_i in queue_list:
        if q_i.task_done():
            q_w.put(q_i.ipv4, q_i.filename) # works
    print(q.qsize())
    sleep(1)
print("queue empty")
q.join()
FLAG_q_alltaskdone = True
q_w.join()

# json.dump(all_ipv4[47][95], open(f"47.95.223.{tn}.json", "w+"))
# hope this work ...
json.dump(all_ipv4, open("ipv4.json", "w+"))