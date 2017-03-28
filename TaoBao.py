
#-*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy
from selenium.webdriver.common.proxy import ProxyType
import  re
import requests
import os
import datetime
import  urllib
import  redis
import  json

# 取代理Ip服务器
rconnection_Proxy = redis.Redis(host='117.122.192.50', port=6479, db=0)
# 代理IP
redis_key_proxy = "proxy:iplist2"

#随机获取代理IP
proxy1 = rconnection_Proxy.srandmember(redis_key_proxy)
proxyjson = json.loads(proxy1)
proxiip = proxyjson["ip"]
#加到PhantomJS中
Proxy = Proxy(
    {
        'proxyType': ProxyType.MANUAL,
        'httpProxy': proxiip  # 代理ip和端口
    }
)
cap = webdriver.DesiredCapabilities.PHANTOMJS.copy()
cap["phantomjs.pagge.settings.resourceTimeout"]=1000
def proxy_Ip():
    # 随机获取代理ip
    sesson = requests.session()
    proxy = rconnection_Proxy.srandmember(redis_key_proxy)
    proxyjson = json.loads(proxy)
    proxiip = proxyjson["ip"]
    sesson.proxies = {'http': 'http://' + proxiip, 'https': 'https://' + proxiip}
    return sesson

class Spider:


    def __init__(self):
        self.page=1
        self.dirName='MMSpider'
        #cap = webdriver.DesiredCapabilities.PHANTOMJS
        #cap = webdriver.DesiredCapabilities.PHANTOMJS.copy()
        #Proxy.add_to_capabilities(cap)
        self.driver=webdriver.PhantomJS(executable_path="F:\Python\Scripts\phantomjs.exe",desired_capabilities=cap)

    def getContent(self,maxPage):
        for index in range(1,maxPage+1):
            self.LoadpageContent(index)

    def LoadpageContent(self,page):

        begin_time=datetime.datetime.now()
        url="https://mm.taobao.com/json/request_top_list.htm?page="+str(page)

        user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0'
        headers = {'User-Agent': user_agent,
                   "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                   }
        self.page += 1
        isValue=True
        while isValue:
            isValue=False
            session = proxy_Ip()
            try:
                #加载页面信息
                req = session.get(url, headers=headers, timeout=30)
                html = req.text
                req.close()
                #html=self.driver(url, headers=headers, timeout=30)
                #html = self.driver(url)
                if html:
                    #正则获取页面有用信息
                    patter_link=re.compile(r'<div[\s\S].*?class="pic-word">[\s\S]*?<img src="(.*?)"[\s\S]*?'
                                           r'<a.*?class="lady-name".*?href="(.*?)".*?>(.*?)</a>[\s\S]*?'
                                           r'<em>.*?<strong>(.*?)</strong>[\s\S]*?'
                                           r'<span>(.*?)</span>' ,re.S)
                    items=re.findall(patter_link,html )

                    index=0
                    for item in items:
                        # 头像，个人评情，名字，年龄，地区
                        print u'前方发现一个MM 好像叫 %s 年龄 %s 来自 %s ' % (item[2],item[3],item[4])
                        print u'%s的个人主页是 %s'%(item[2],item[1])
                        print u'继续获取详情页面数据......'
                        detaiPage=item[1]
                        name=item[2]
                        #获取下级页面中详细数据
                        self.geDataPage(detaiPage,name,begin_time)

                else:
                    print  '没有发现URl内容'
                    break
            except Exception,e:
                print '不知道什么错 %s' % e
    #页面详情，使用PhantomJS
    def geDataPage(self,url,name,begin_time):
        #得到URl
        url='http:'+url
        #加载URl
        self.driver.get(url)
        #用Xpath获取信息
        base_msg=self.driver.find_elements_by_xpath(r'//div[@class="mm-p-info mm-p-base-info"]/ul/li')
        #base_msg = self.driver.find_elements_by_xpath(r'//div[@class="mm-p-model-info-left-top"]//img')
        brief=''
        #print base_msg
        for item in base_msg:
            print item.text
            brief+=item.text+'\n'
            #获取头像路径
        try:

            #icon_url=self.driver.find_elements_by_xpath(r'//div[@class="mm-p-model-info-left-top"]//img/@src').click()
            icon_url = self.driver.find_elements_by_xpath(r'//img[@id="J_MmPheader"]')
            #icon_url = self.driver.find_elements_by_xpath(r'//img[@id="J_MmPheader"]')
            #icon_url=icon_url.get_attribute('src')
            #icon_urls=icon_url.('src')

            for i in icon_url:
                icon_url =i.get_attribute('src')
                print icon_url

        except BaseException,e:
            print e.message

        #保存地址
        dir=self.dirName+'/'+name
        self.mkdir(dir)
        try:
            #保存头像
            self.saveIcon(icon_url,dir,name)
        except Exception,e:
            print u'保存头像出错 %s'% e.message
        #相册URl
        images_url=self.driver.find_element_by_xpath(r'//ul[@class="mm-p-menu"]/li[1]/span/a')
        imagesUrl=images_url.get_attribute('href')
        #for i in images_url:
            #imagesUrl= i.get_attribute('href')
        print  imagesUrl
        try:
            #保存相片方法
            self.getAllImage(imagesUrl,name)
        except Exception,e:
            print u'获取所有相册异常 %s' % e.message
    #获取所有图片
    def getAllImage(self,images_url,name):
        print u'%s 的相册路径 %s' %(name,images_url)
        self.driver.get(images_url)
        #只获取第一个相册
        photos=self.driver.find_element_by_xpath('//div[@class="mm-photo-cell-middle"]//h4/a')
        photos_url=photos.get_attribute('href')

        print u'第一个相册地址 %s' %photos_url

        #进入相册页面获取相册内容
        self.driver.get(photos_url)
        images_all=self.driver.find_elements_by_xpath('//div[@class="mm-photoimg-area"]/a/img')

        if(len(images_all)==0):
            print u'该相册没有找到相片'
        else:
            self.saveImgs(images_all,name)
    def saveImgs(self,images,name):
        index=1
        print  u'%s 的相册有%s张照片，正在尝试全部下载.....'%(name,len(images))
        try:
            for imageUrl in images:
                splitPath=imageUrl.get_attribute('src').split('.')
                fTail=splitPath.pop()
                if len(fTail)>3:
                    fTail="jpg"
                fileName=self.dirName+'/'+name+'/'+name+str(index)+'.'+fTail
                print u'下载图片地址 %s'% fileName

                self.saveImg(imageUrl.get_attribute('src'),fileName)
                index+=1
        except Exception,e:
            print "保存图像出错 %s" % e
    #保存头像
    def saveIcon(self,url,dir,name):
        print u'头像地址 %s %s '%(url,name)

        splitPath=url.split('.')
        #for i in splitPath:
            #print i
        fTail=splitPath.pop()
        fileName=dir+'/'+name+'.'+fTail
        print fileName
        self.saveImg(url,fileName)
    #写入图片
    def saveImg(self,imageUrl,fileName):
        print imageUrl
        u=urllib.urlopen(imageUrl)
        data=u.read()
        f=open(fileName,'wb')
        f.write(data)
        f.close()
        print  '保存头像成功'
    def saveBrief(self,content,dir,name,speed_time):
        speed_time=u'当前MM耗时'+str(speed_time)
        content=content+'\n'+speed_time
        fileName=dir+'/'+name+''.txt
        f=open(fileName,'w+')
        print u'正在获取%s 的个人信息保存到%s'(name,fileName)
        f.write(content.encode('utf-8'))
    #创建目录
    def mkdir(self,path):
        path=path.strip()
        print u'创建目录%s'%path
        if os.path.exists(path):
            return False
        else:
            os.makedirs(path)
            return True








if __name__=='__main__':
    #创建Spider对像
    spider=Spider()
    #调用方法
    spider.getContent(1)