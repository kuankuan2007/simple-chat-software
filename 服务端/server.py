import json
import logging
import os
import longPolling.server
dateFormater="%Y-%m-%d %H:%M:%S"
logFormater="[%(asctime)s] [%(name)s] [%(threadName)s] [Line%(lineno)d] [%(levelname)s]: %(message)s"
logging.basicConfig(level=logging.DEBUG,format=logFormater,datefmt=dateFormater)
LauncherLog = logging.getLogger('Launcher')
LauncherLog.debug("try launching with the data in config.json")
try:
    with open("config.json",encoding="utf-8") as f:
        config = json.load(f)
except Exception as err:
    LauncherLog.critical("Could not load config.json %s:%s"%(err.__class__.__name__,str(err)))
    os._exit(-1)

def send(self,user,data):
    sendLog = logging.getLogger(f'send/{user}')
    try:
        body=json.loads(data.decode("utf-8","target"))
        assert type(body)==dict
        print(body["user"])
        self.send(body["user"],json.dumps({
            "message":body["message"],
            "time":body["time"],
            "otherId":user
        }).encode())
    except BaseException as err:
        sendLog.warning(f"{err.__class__.__name__}:{err}")
connection=longPolling.server.BothwayServer(config.get("host"),config["port"],receive=send,threaded=False,started=False)
connection.start()