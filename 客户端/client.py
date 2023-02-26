import tkinter
from tkinter import ttk,messagebox,simpledialog
import logging
import json
import os
import time
import math
import threading
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import requests
import base64
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
def close():
    closeLog=logging.getLogger(f'close')
    try:
        requests.post("http://%s:%d/logout/%s"%user)
        closeLog.info("try closing connection")
    except:
        pass
dateFormater="%Y-%m-%d %H:%M:%S"
logFormater="[%(asctime)s] [%(name)s] [%(threadName)s] [Line%(lineno)d] [%(levelname)s]: %(message)s"
logging.basicConfig(level=logging.DEBUG,format=logFormater,datefmt=dateFormater)
LauncherLog = logging.getLogger('Launcher')
LauncherLog.debug("try launching with the data in config.json")
try:
    with open("config.json",encoding="utf-8") as f:
        config = json.load(f)
except BaseException as err:
    LauncherLog.critical("Could not load config.json %s:%s"%(err.__class__.__name__,str(err)))
    os._exit(-1)
def connect():
    global user,key
    connectLog = logging.getLogger('connect')
    connectLog.info("connect thread started")
    tempWin = tkinter.Tk()
    tempWin.withdraw()
    while True:
        connectLog.info("waiting for username")
        tempuser=simpledialog.askstring("用户名","请输入您用户名",parent=tempWin)
        if tempuser==None:
            connectLog.critical("The user canceled the input")
            os._exit(-1)
        if len(tempuser)<=2:
            connectLog.info("short username")
            messagebox.showinfo("用户名不合法","用户名至少需要3个字符")
            continue
        connectLog.info("connect for login [%s]"%tempuser)
        try:
            retsult=requests.post("http://%s:%d/login/"%(config["host"],config["port"]),json={"user":tempuser})
        except BaseException as err:

            connectLog.warning("connect err %s:%s"%(err.__class__.__name__,str(err)))
            messagebox.showerror("连接错误","无法连接至服务器")
            continue
        if retsult.status_code!=200:
            connectLog.warning("connection died [%d]"%retsult.status_code)
            messagebox.showerror("连接错误","无法连接至服务器")
            continue
        try:
            retsult=json.loads(retsult.content.decode("utf-8"))
        except:
            connectLog.warning("wrong anwser")
            messagebox.showerror("数据错误","服务器返回了错误的数据")
            continue
        if retsult["code"]==1:
            user=tempuser
            key=retsult["key"]
            mainScreen.title(user+" - 客户端")
            lastEmpty=True
            while True:
                obj={
                    "lastEmpty":lastEmpty
                }
                try:
                    connectLog.info("start next request")
                    retsult=requests.post("http://%s:%d/receive/%s"%(config["host"],config["port"],user),json=obj,timeout=30)
                    lastEmpty=False
                except requests.Timeout:
                    connectLog.info("request timeOut")
                except BaseException as err:
                    connectLog.critical("request error %s:%s"%(err.__class__.__name__,str(err)))
                else:
                    if retsult.status_code!=200:
                        connectLog.critical("request staus error %d"%(retsult.status_code))
                    try:
                        retsult=json.loads(retsult.content.decode("utf-8") )
                    except BaseException as err:
                        connectLog.critical("result decode error %s:%s"%(err.__class__.__name__,str(err)))
                    else:
                        if retsult.get("code")==1:
                            connectLog.info("receive a message")
                            try:
                                retsult["message"]=decrypt(retsult["message"],key)
                                retsult["message"]=retsult["message"][:retsult["message"].rfind("$")]
                            except:
                                connectLog.info("key error")
                                retsult["message"]="[KEY ERROR]"+retsult["message"]
                            history.insert(0,Message(retsult["otherId"],"in",retsult["time"],retsult["message"]))
                            reDraw(1)
                            lastEmpty=False
        else:
            connectLog.info("username was used")
            messagebox.showinfo("用户错误","用户名已被使用或无法被识别")
    tempWin.destroy()
    



LauncherLog.info("start connect thread")
threading.Thread(target=connect,daemon=True).start()

key=""
history=[]
def resetEntry(entry,text="",readonly=False):
    entry.config(state="normal")
    entry.delete(0,tkinter.END)
    entry.insert(0,text)
    if readonly:
        entry.config(state="readonly")
    return entry
class Message:
    def __init__(self,otherId,type,time,message):
        self.otherId=otherId
        self.type=type
        self.time=time
        self.message=message
    def draw(self,num):
        resetEntry(historyEntrys[num][0],time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(self.time)),readonly=True)
        resetEntry(historyEntrys[num][1],self.otherId,readonly=True)
        resetEntry(historyEntrys[num][2],["<-","->"][self.type=="in"],readonly=True)
        resetEntry(historyEntrys[num][3],self.message,readonly=True)
LauncherLog.debug("creating window")
mainScreen =tkinter.Tk()
mainScreen.iconbitmap("logo.ico")
mainScreen.title("客户端")
historyBox = tkinter.Frame(mainScreen)
historyBox.grid(row=0,column=0,padx=2,pady=5)
historyTitle=tkinter.Frame(historyBox)
historyTitle.grid(row=0,column=0)

resetEntry(ttk.Entry(historyTitle,width=17),"时间",readonly=True).grid(row=0,column=0)
resetEntry(ttk.Entry(historyTitle,width=16),"对象",readonly=True).grid(row=0,column=1)
resetEntry(ttk.Entry(historyTitle,width=4),"方向",readonly=True).grid(row=0,column=2)
resetEntry(ttk.Entry(historyTitle,width=40),"消息",readonly=True).grid(row=0,column=3)

historyEntrys=[]
for i in range(config["pageHeight"]):
    messageLine=tkinter.Frame(historyBox)
    messageLine.grid(row=i+1,column=0)
    historyEntrys.append((
        resetEntry(ttk.Entry(messageLine,width=17,name="time"),"",readonly=True),
        resetEntry(ttk.Entry(messageLine,width=16,name="otherId"),"",readonly=True),
        resetEntry(ttk.Entry(messageLine,width=4,name="type"),"",readonly=True),
        resetEntry(ttk.Entry(messageLine,width=40,name="message"),"",readonly=True)
    ))
    for j in range(4):
        historyEntrys[-1][j].grid(row=0,column=j)

pageNum=tkinter.StringVar(historyBox)
pageNum.set("第1页,共1页")
nowpage=1

tkinter.Label(historyBox,textvariable=pageNum).grid(row=config["pageHeight"]+1,column=0)

buttonBox=tkinter.Frame(historyBox)
buttonBox.grid(row=config["pageHeight"]+2,column=0,sticky="E")
def pageUp():
    global nowpage
    nowpage-=1
    reDraw(nowpage)
def pageDown():
    global nowpage
    nowpage+=1
    reDraw(nowpage)
pageUpButton=ttk.Button(buttonBox,text="上一页",command=pageUp,state="disabled")
pageUpButton.grid(row=0,column=0)
pageDownButton=ttk.Button(buttonBox,text="下一页",command=pageDown,state="disabled")
pageDownButton.grid(row=0,column=1)


def reDraw(page):
    if (page-1)*config["pageHeight"]>=len(history):
        pageDownButton.config(state="disabled")
        return
    if page==1:
        pageUpButton.config(state="disabled")
    else:
        pageUpButton.config(state="normal")
    if page*config["pageHeight"]>=len(history):
        pageDownButton.config(state="disabled")
    else:
        pageDownButton.config(state="normal")
    for i in range(config["pageHeight"]):
        if (page-1)*config["pageHeight"]+i>=len(history):
            for j in range(4):
                resetEntry(historyEntrys[i][j],"",readonly=True)
        else:
            history[(page-1)*config["pageHeight"]+i].draw(i)
    pageNum.set("第%d页,共%d页"%(page,math.ceil(len(history)/config["pageHeight"])))



reDraw(1)

def send():
    sendLog=logging.Logger("send")
    message=sendEntry.get()
    otherId=aimEntry.get()
    if not message:
        sendLog.info("empty message")
        return
    if not otherId:
        sendLog.info("empty aim")
        return
    
    if not key:
        sendLog.info("key is unknown")
        return
    obj={
        "message":encrypt(message+"$",key),
        "user":otherId,
        "time":time.time()
    }
    sendLog.debug("try sending to servers")
    try:
        retsult=requests.post("http://%s:%d/send/%s"%(config["host"],config["port"],user),json=obj)
    except BaseException as err:
        sendLog.error("send fail,%s:%s"%(err.__class__.__name__,str(err)))
        messagebox.showerror("发送失败","连接服务器出错，请重试")
        return
    try:
        retsult=json.loads(retsult.content.decode("utf-8"))
    except:
        sendLog.error("wrong answer")
        messagebox.showerror("发送失败","服务器返回不可识别")
    if retsult.get("code")==1:
        sendLog.info("successfully send message to%s\n%s"%(obj["user"],obj["message"]))
        resetEntry(sendEntry,"")
        resetEntry(aimEntry,"")
        history.insert(0,Message(otherId,"out",obj["time"],message))
        reDraw(1)
    else:
        if retsult.get("becauseOf")=="user":
            sendLog.info("user not found")
            messagebox.showinfo("发送失败","用户不存在")
        else:
            sendLog.info("return code error")
            messagebox.showerror("发送失败","服务器未能发送消息，请重试")



    


sendBox=tkinter.Frame(mainScreen)
sendBox.grid(row=1,column=0,padx=2,pady=5)
sendEntry=ttk.Entry(sendBox,width=60)
sendEntry.grid(row=0,column=0,sticky="W",columnspan=3)
tkinter.Label(sendBox,text="发送给:").grid(row=1,column=0,padx=2,sticky="E")
aimEntry=ttk.Entry(sendBox,width=16)
aimEntry.grid(row=1,column=1,sticky="W")
sendButton=ttk.Button(sendBox,text="发送",command=send)
sendButton.grid(row=1,column=2,sticky="E")

LauncherLog.info("start mainloop")
mainScreen.mainloop()
close()