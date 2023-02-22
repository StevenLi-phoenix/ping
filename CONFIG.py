import requests

LEVEL = 20  # info: 20
LogDirectionary = "./log"
ICMP_ECHO_REQUEST = 8
RETRY_TIMES = 3
LOOPTIMEOUTSEC = 20
DELAYONCRITICALERROR = 60

LOCAL_SERVER_IP = "http://127.0.0.1:8001" # FOR LOCAL SERVRE ONLY
INTRA_SERVER_IP = "http://172.16.82.60:8001" # FOR INTRANET
INTER_SERVER_IP = "http://47.95.223.74:8001" # FOR PUBLIC address

try:
    if requests.get(LOCAL_SERVER_IP + "/ping", timeout=2).status_code == 200:
        SERVER_IP = LOCAL_SERVER_IP
except:
    try:
        if requests.get(INTRA_SERVER_IP + "/ping", timeout=2).status_code == 200:
            SERVER_IP = INTRA_SERVER_IP
    except:
        SERVER_IP = INTER_SERVER_IP
