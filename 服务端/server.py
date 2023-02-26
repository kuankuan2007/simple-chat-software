import json
import flask
import logging
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import random
import time
import threading
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
app = flask.Flask(__name__)
messages={"root":[]}
keys={}
lastTime={}
threads={}
def encrypt(pwd, key):
    pwd = pwd.encode('utf-8')
    key = key.encode('utf-8')
    cryptos = AES.new(key, AES.MODE_ECB)
    msg = cryptos.encrypt(pad(pwd, 16))
    msg = base64.b64encode(msg)
    msg=msg.decode('utf-8',"target")
    return msg
def decrypt(word, key):
    word = base64.b64decode(word)
    key = key.encode("utf-8")
    cipher = AES.new(key, AES.MODE_ECB)
    a = cipher.decrypt(word)
    a = a.decode('utf-8', 'ignore')
    return a
@app.route('/logout/<name>', methods=['POST'])
def logout(name):
    if name in messages:
        del messages[name]
@app.route('/receive/<name>', methods=['POST'])
def receive(name):
    t=time.time()
    lastTime[name] = t
    receiveLog = logging.getLogger(f'receive/{name}')
    if name not in messages:
        receiveLog.info(f"user {name} not found")
        return "",404
    receiveLog.debug("waiting")
    while threads.get(name):
        time.sleep(0.3)
    receiveLog.debug("mainloop")
    threads[name] = True
    try:
        body=json.loads(flask.request.stream.read().decode("utf-8","target"))
    except:
        body={"lastEmpty":True}
    if not body["lastEmpty"] and len(messages[name]):
        del messages[name][0]
    while True:
        time.sleep(0.1)
        if len(messages[name]):
            returnValue=messages[name][0]
            returnValue["message"]=encrypt(returnValue["message"]+"$",keys[name])
            returnValue["code"]=1
            threads[name] = False
            print(returnValue)
            receiveLog.info("new message")
            return json.dumps(returnValue)
        if time.time()-t>30:
            receiveLog.debug("timeout")
            threads[name] = False
            return {"code":0}
@app.route('/send/<name>', methods=['POST'])
def send(name):
    sendLog = logging.getLogger(f'send/{name}')
    if name not in messages:
        sendLog.info("nam not found")
        return "",404
    try:
        body=json.loads(flask.request.stream.read().decode("utf-8","target"))
    except:
        sendLog.warning("decode error")
        return json.dumps({"code":-1,"becauseOf":"decode"})
    if all(value in body for value in ["user","time","message"]):
        try:
            body["message"]=decrypt(body["message"],keys[name])
        except:
            sendLog.info("ky error")
        body["message"]=body["message"][:body["message"].rfind("$")]
        body["otherId"]=name
        if body["user"] not in messages:
            sendLog.warning("user %s is not found"%body["user"])
            return json.dumps({"code":0,"becauseOf":"user"}),200
        messages[body["user"]].append(body)
        sendLog.info("successfully send message to%s\n%s"%(body["user"],body["message"]))
        return json.dumps({"code":1}),200
    else:
        return json.dumps({"code":0,"becauseOf":"args"}),200
@app.route('/login/', methods=['POST'])
def login():
    loginLog = logging.getLogger('login')
    try:
        body=json.loads(flask.request.stream.read().decode("utf-8","target"))
    except:
        return json.dumps({"code":-1})
    loginLog.info("login "+str(body.get("user")))
    if body.get("user","root") not in messages:
        charList="1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        s=random.choices(charList,k=16)
        value="".join(s)
        messages[body["user"]]=[]
        keys[body["user"]]=value
        lastTime[body["user"]]=time.time()
        loginLog.info("%s successfully login with secret key [%s]"%(str(body.get("user")),value))
        return json.dumps({"code":1,"key":value})
    else:
        loginLog.info("%s login failed,it was used")
        return json.dumps({"code":0})
LauncherLog.info("start flask server")
def control():
    control=logging.Logger("control")
    while True:
        li=[]
        time.sleep(5)
        for i in messages:
            if time.time() - lastTime.get(i,0) >= 60:
                li.append(i)
        for i in li:
            try:
                control.warning("del user "+i)
                del messages[i]
            except:
                control.error("fail to del user "+i)
threading.Thread(target=control,daemon=True).start()
app.run(config.get("host"),config["port"],threaded=True)