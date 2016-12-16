# coding=u8

from __future__ import division
import sys
import os
import time
import myurllib
import socket
import re
import wsort


class Timer(object):
    '线程内计时器类'
    def __init__(self):
        self.timer = 0
    def start(self):
        self.timer = time.time()
    def now(self):
        if (self.timer!=0):
            return time.time() - self.timer
        else:
            print('[Timer] Start this timer first !')
            return False
    def end(self):
        self.timer = 0


class Downloader(object):
    def __init__(self,url,path,index):
        self.url = url
        self.path = path
        self.index = index
        self.__timer = Timer()
        self.__timer_total = Timer()
        self.__size_last = 0
        self.blockNum = 0
        self.flag_finish = False

    def report(self, url, blockNum, blockSize, totalSize): 
        self.blockNum = blockNum;
        downloadSize = blockNum*blockSize
        if downloadSize > totalSize:
            downloadSize = totalSize
        percent = blockNum*blockSize*100/totalSize

        if(self.__size_last > downloadSize): #重新请求设置
            print('size_last')
            self.__size_last = 0
            self.__timer_total.start()
            self.__timer.start()
        
        time_pass = self.__timer.now()
        if(time_pass>0.5):
            self.__timer.start()
            size_diff = downloadSize - self.__size_last
            self.__size_last = downloadSize
            speed = size_diff/time_pass/1024
            if(totalSize<(1024*1024*10)):
                print('{} ({}/{}) {:.1f}% ({:.1f}KB/{:.1f}KB) {:.1f}KB/s'.format(url.split('/')[-1],self.index,tsNum,percent,downloadSize/1024,totalSize/1024,speed))
            else:
                print('{} ({}/{}) {:.1f}% ({:.1f}MB/{:.1f}MB) {:.1f}KB/s'.format(url.split('/')[-1],self.index,tsNum,percent,downloadSize/1024/1024,totalSize/1024/1024,speed))
        if(downloadSize==totalSize):
            speed = totalSize/(self.__timer_total.now())/1024
            self.__timer.end()
            self.__timer_total.end()
            if(totalSize<(1024*1024*10)):
                print('{} ({}/{}) 100% ({:.1f}KB/{:.1f}KB) Complete with averspeed {:.1f}KB/s'.format(url.split('/')[-1],self.index,tsNum,downloadSize/1024,totalSize/1024,speed))
            else:
                print('{} ({}/{}) 100% ({:.1f}MB/{:.1f}MB) Complete with averspeed {:.1f}KB/s'.format(url.split('/')[-1],self.index,tsNum,downloadSize/1024/1024,totalSize/1024/1024,speed))       

    def start(self):
        print('Download start with [{}] ...'.format(self.url))
        self.__timer.start()
        self.__timer_total.start()
        state = myurllib.urlretrieve(self.url, self.path, reporthook=self.report)
        if not state:
            print('Download timeout, restart ...')
            self.start()
            return
        self.flag_finish = True
        print("Download [{}] completely, saved to [{}]\n".format(self.url,self.path) + '')


def getfiles(dir,ext=0):
    for root, dirs, origin_files in os.walk(dir):
        files = []
        for file in origin_files:
            if root[-1]!='/' and root[-1]!='\\':
                file_abs = root+os.sep+file
            else:
                file_abs = root+file
            if ext:
                if(file_abs.endswith(ext)):
                    files.append(file_abs)
            else:
                files.append(file_abs)
        return files

def combine(filename,dirpath):
    combine = dirpath+'/'+filename
    files = getfiles(dirpath,'ts')
    files = wsort.wsort(files)
    if combine in files:
        files.remove(combine)
    data = ''
    with open(combine,'wb') as f: #清空
        f.write('')
    for file in files:
        if os.path.split(file)[1]==filename:
            continue
        with open(file,'rb') as f:
            data=f.read()
        with open(combine,'ab') as f: #追加
            f.write(data)
        print('combined {} ...'.format(file))

def isset(var):
    try:
        type(var)
        return True
    except NameError:
        return False

def cmkdir(path):
        try:
            if(os.path.exists(path)==False or os.path.isdir(path)==False):
                os.mkdir(path)
        except:
            traceback.print_exc()
            return False
        return True

def get(url):
    try:
        res = myurllib.urlopen(url)
        return res
    except:
        print('[get] timeout retry')
        return get(url)

def isGood(url):
    try:
        res = myurllib.urlopen(url) #测试
        if(res.code == 404):
            return False
        else:
            return True
    except :
        print('[isGood] timeout retry')
        return isGood(url)
        
def getTsNum(id):
    i = 0
    url_pre = 'http://dlvod.cdn.zhanqi.tv/videonew/hls/special/'+id+'/'+id+'-' 
    while(True):
        i = i+1
        url = url_pre+str(i)+'.ts' 
        save_path = './'+url.split('/')[-1]
        if not isGood(url):
            break
        print('{} is good'.format(url))
    return i-1

def download(vid):
    global tsNum
    # 创建文件夹
    dirname = vid.replace('/','-')
    dirpath = './video/'+dirname
    cmkdir('./video/')
    cmkdir(dirpath)
    # 获取必须变量
    print('Start download with vid: {}'.format(vid))
    print('Getting necessary viariables ...')
    url = 'https://www.zhanqi.tv/videos/'+str(vid)+'.html'
    res = get(url)
    html = res.read()
    vid_short = vid.split('/')[-1]
    reg = re.search('('+vid_short+'_.+?)\\\\',html,re.S)
    vid_all = reg.groups(0)[0]
    url_pre = 'http://dlvod.cdn.zhanqi.tv/videonew/hls/special/'+vid_all+'/'+vid_all+'-'
    #获取视频分段数目
    print('Getting .ts number ...')
    #tsNum = 5
    #start = 318
    if 'tsNum' not in locals().keys():
        tsNum = getTsNum(vid_all)
    if 'start' not in locals().keys():
        start = 1
    print('Got .ts number: {} ...'.format(tsNum))
    # 逐段下载
    for i in range(start,tsNum+1):
        url = url_pre+str(i)+'.ts'
        filename = url.split('/')[-1]
        save_path = dirpath+'/' + filename
        downloader = Downloader(url,save_path,i)
        downloader.start()
    print('All parts download successfully !')
    # 合并文件
    print('Combine files ... {}'.format(vid))
    combine(dirname+'.ts',dirpath)
    print('Combine success {} !'.format(vid))
    print('\n')

def main():
    if len(sys.argv)>1:
        vid = sys.argv[1]
        if None!=re.match('danji/\d{4}/\d{1,2}/\d+',vid):
            download(vid)
        else:
            print('Wrong vid syntax!')
    else:
        vid_list = [
            'danji/2015/11/50099'
        ]
        for vid in vid_list:
            download(vid)

if __name__ == '__main__':
    main()


