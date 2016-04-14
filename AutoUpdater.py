# -*- coding: UTF-8 -*-
'''
Created on 2016-03-30
@author: solomonlu(mengyi.lu)
'''
from Tkinter import *
import ttk
import tkMessageBox
import os
import json
import hashlib
import urllib
import urllib2
import threading
import subprocess

localPath = "./"
serverPath = "http://192.168.101.67:8081/BlackShield/"
localDirectory = "WindowsNoEditor"
versionFile = "version.txt"
md5File = "resource.md5.txt"
exeFile = "StarVR_V1.exe"


def calcMD5(fileName):
    m = hashlib.md5()
    n = 1024*4
    file = open(fileName,"rb")
    while True:  
        buf = file.read(n)  
        if buf:  
            m.update(buf)  
        else:  
            break  
    file.close()
    md5value = m.hexdigest()
    return md5value


def getLocalFilesMD5():
    localMD5Filename = localPath + versionFile

    #if exist,read from file
    if os.path.exists(localFileFolder):
        f = open(filename,'r')
        content = f.read()
        fileList = json.loads(content)
        f.close()
        return fileList
    #if not,scan whole path
    else:
        fileList = {}
        directory = localDirectory
        if directory[-1] == '\\' or directory[-1] == '/':
            directory = directory[:-1]
        realDirectory = os.path.split(directory)[1]

        def findFile(arg,dirname,files):
            for file in files:
                file_path=os.path.join(dirname,file)
                if os.path.isfile(file_path):
                    md5 = calcMD5(file_path)
                    size=os.path.getsize(file_path)
                    file_path = file_path.replace(directory,realDirectory)
                    file_path = file_path.replace("\\", "/")
                    fileList[file_path] = (md5,size)
                    #print ("find file:%s,md5:%s,size:%d" %(file_path,md5,size))
        os.path.walk(directory,findFile,())
        return fileList


def getServerFilesMD5():
    try:
        url =  serverPath + md5File
        page = urllib2.urlopen(url, timeout=10)
        data = page.read()
        files = json.loads(data)
        return files
    except urllib2.URLError, ex:
        errMsg = u"读取服务器md5文件失败，错误[%s]，错误代码:[%d]" % (ex,ex.code)
        tkMessageBox.showerror(title=u"发生错误", message=errMsg)
        exit(-1)


def downloadProcedure(diffFiles,totalDownloadBytes,serverVersionStr,serverFiles,downloadTotalTips,progressTotal,downloadCurrentTips,progressCurrent,startGameButton):
    currentDownloadBytes = 0

    def SingleFileDownloadProgressCallback(a,b,c,currentDownloadBytes,totalDownloadBytes,downloadTotalTips,progressTotal,downloadCurrentTips,progressCurrent):
        curDownBytes = a*b
        if curDownBytes > c:
            curDownBytes = c
        
        downloadTotalTips["text"] = "total download: %d/%d" % (currentDownloadBytes + curDownBytes , totalDownloadBytes)
        downloadCurrentTips["text"] = "current download: %d/%d" % (curDownBytes,c)
        progressTotal["value"] = currentDownloadBytes + curDownBytes
        progressCurrent["value"] = curDownBytes

    #download diff files
    for k,v in diffFiles.items():
        serverFileLocation = os.path.join(serverPath,k)
        localFileLocation = os.path.join(localPath,k)
        localFileFolder = os.path.dirname(localFileLocation)
        if not os.path.exists(localFileFolder):
            os.makedirs(localFileFolder)

        progressCurrent["maximum"] = v[1]
        urllib.urlretrieve(serverFileLocation,localFileLocation,lambda
                a,b,c:SingleFileDownloadProgressCallback(a,b,c,currentDownloadBytes,totalDownloadBytes,downloadTotalTips,progressTotal,downloadCurrentTips,progressCurrent))
        currentDownloadBytes += v[1]

    #done
    startGameButton["state"]=NORMAL

    #save to file
    file1 = open(localPath + versionFile,"w")
    file1.write(serverVersionStr)
    file1.close()

    file2 = open(localPath + md5File,"w")
    file2.write(json.dumps(serverFiles))
    file2.close()


def matchVersion(localVersionStrLabel,serverVersionStrLabel,startGameButton,downloadTotalTips,progressTotal,downloadCurrentTips,progressCurrent):
    localVersionStr = ""
    serverVersionStr = ""

    filename = localPath + versionFile
    if os.path.exists(filename):
        #if file exist,say let's use it to judge whether need update
        f = open(filename,'r')
        localVersionStr = f.read()
        f.close()
    else:
        #if file not exist,then use md5 to judge whether need update
        localVersionStr = "unknown"
    localVersionStr = localVersionStr.strip()
    localVersionStrLabel["text"] = localVersionStr

    url = serverPath + versionFile
    try:
        page = urllib2.urlopen(url, timeout=10)
        serverVersionStr = page.read()
    except urllib2.URLError, ex:
        errMsg = u"读取服务器版本文件失败，错误[%s]，错误代码:[%d]" % (ex,ex.code)
        tkMessageBox.showerror(title=u"发生错误", message=errMsg)
        exit(-1)
    serverVersionStr = serverVersionStr.strip()
    serverVersionStrLabel["text"] = serverVersionStr

    #if version str is match, no need do anything
    if localVersionStr == serverVersionStr:
        startGameButton["state"]=NORMAL
        return

    #calc diff files
    localFiles = getLocalFilesMD5()
    serverFiles = getServerFilesMD5()
    diffFiles = {}
    totalDownloadBytes = 0
    for k,v in serverFiles.items():
        if not k in localFiles:
            diffFiles[k] = v
            totalDownloadBytes += v[1]
        else:
            # if md5 is not equal,should download too
            if localFiles[k][0] != v[0]:
                diffFiles[k] = v
                totalDownloadBytes += v[1]
    progressTotal["maximum"] = totalDownloadBytes

    #start a thread to download
    threading.Thread(target =
            lambda:downloadProcedure(diffFiles,totalDownloadBytes,serverVersionStr,serverFiles,downloadTotalTips,progressTotal,downloadCurrentTips,progressCurrent,startGameButton)).start()



def startGame():
    exeFilePath = os.path.join(localDirectory,exeFile)
    subprocess.Popen(exeFilePath)
    exit(0)


def main():
    guiRoot = Tk()
    guiRoot.geometry('450x250')
    guiRoot.title('Auto Updater')
    guiRoot.resizable(False,False)
    
    guiRoot.withdraw()    #hide window
    screen_width = guiRoot.winfo_screenwidth()
    screen_height = guiRoot.winfo_screenheight() - 100    #under windows, taskbar may lie under the screen
    guiRoot.resizable(False,False)
 


    #version frame
    versionFrame = Frame(guiRoot, height=150, width=450)
    versionFrame.pack()
    localVersionTips = Label(versionFrame,text="local version:")
    localVersionTips.pack()
    localVersionStr = Label(versionFrame,text="")
    localVersionStr.pack()
    serverVersionTips = Label(versionFrame,text="server version:")
    serverVersionTips.pack()
    serverVersionStr = Label(versionFrame,text="")
    serverVersionStr.pack()

    #progress frame
    progressFrame = LabelFrame(guiRoot, height=150, width=450)
    progressFrame.pack()
    downloadTotalTips = Label(progressFrame,text="total download:")
    downloadTotalTips.pack()
    progressTotal = ttk.Progressbar(progressFrame, orient="horizontal",
            length=500, mode="determinate",value=0,maximum=100)
    progressTotal.pack()
    downloadCurrentTips = Label(progressFrame,text="current download:")
    downloadCurrentTips.pack()
    progressCurrent = ttk.Progressbar(progressFrame, orient="horizontal",
            length=500, mode="determinate",value=0,maximum=100)
    progressCurrent.pack()

    #start button
    Label(guiRoot,text="").pack()
    startGameButton=Button(guiRoot,text = 'Start Game',command = startGame, state=DISABLED)
    startGameButton.pack()
    

    guiRoot.after(500,lambda :
            matchVersion(localVersionStr,serverVersionStr,startGameButton,downloadTotalTips,progressTotal,downloadCurrentTips,progressCurrent))


    guiRoot.update_idletasks()
    guiRoot.deiconify()    #now window size was calculated
    guiRoot.withdraw()     #hide window again
    guiRoot.geometry('%sx%s+%s+%s' % (guiRoot.winfo_width() + 10, guiRoot.winfo_height() + 10, (screen_width - guiRoot.winfo_width())/2, (screen_height - guiRoot.winfo_height())/2) )    #center window on desktop
    guiRoot.deiconify()

    mainloop()

if __name__ == "__main__":
    main()
