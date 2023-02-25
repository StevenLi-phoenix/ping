import requests
import CONFIG

ip1 = 153
ip2 = ['111',
 '129',
 '147',
 '165',
 '183',
 '201',
 '219',
 '237',
 '255',
 '120',
 '138',
 '156',
 '174',
 '192',
 '210',
 '228',
 '246']
code = "0"

for ips2 in ip2:
    id = ip1*256+int(ips2)
    result = requests.get(CONFIG.INTER_SERVER_IP + f"/revise?id={id}&code={code}")
    print(f"/revise?id={id}&code={code}:{result.status_code},{result.content}")