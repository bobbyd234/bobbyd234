# -*- coding: utf-8 -*-
import ssl
import urllib
import urllib2
import datetime
import time
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
import base64
from BeautifulSoup import BeautifulStoneSoup, BeautifulSoup, BeautifulSOAP
try:
    import json
except:
    import simplejson as json
import SimpleDownloader as downloader

addon = xbmcaddon.Addon('plugin.video.plad')
addon_version = addon.getAddonInfo('version')
profile = xbmc.translatePath(addon.getAddonInfo('profile').decode('utf-8'))
home = xbmc.translatePath(addon.getAddonInfo('path').decode('utf-8'))
REV = os.path.join(profile, 'list_revision')
icon = os.path.join(home, 'icon.png')
FANART = os.path.join(home, 'fanart.jpg')
downloader = downloader.SimpleDownloader()
debug = addon.getSetting('debug')
PADLuser = addon.getSetting('PADLusername')
PADLpass = addon.getSetting('PADLpassword')
cookieDetails = addon.getSetting('cookieDetails')
authDetails = addon.getSetting('authDetails')
PLADDir = 'https://gonna.mobi/premium/wp/epg/'
PLADVar = '?wmsAuthSign='


def addon_log(string):
    if debug == 'true':
        xbmc.log("[addon.live.streams-%s]: %s" %(addon_version, string))


def makeRequest(url, headers=None):
        try:
            if headers is None:
                headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0', 'Cookie': cookieDetails}
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            data = response.read()
            response.close()
            return data
        except urllib2.URLError, e:
            addon_log('URL: '+url)
            if hasattr(e, 'code'):
                addon_log('We failed with error code - %s.' % e.code)
                xbmc.executebuiltin("XBMC.Notification(LiveStreams,We failed with error code - "+str(e.code)+",10000,"+icon+")")
            elif hasattr(e, 'reason'):
                addon_log('We failed to reach a server.')
                addon_log('Reason: %s' %e.reason)
                xbmc.executebuiltin("XBMC.Notification(LiveStreams,We failed to reach a server. - "+str(e.reason)+",10000,"+icon+")")


def getSources():
        addDir('Premier AD Live',PLADDir,15,icon,FANART,'','','','')

def get_xml_database(url, cookieInfo, browse=False):
        addon_log('using cookie - '+cookieInfo)
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0', 'Cookie': cookieInfo}
        if url is None:
            url = PLADDir
        soup = BeautifulSoup(makeRequest(url, headers), convertEntities=BeautifulSoup.HTML_ENTITIES)
        try:
          for i in soup('a'):
              href = i['href']
              if not href.startswith('?'):
                  name = i.string
                  if name not in ['Parent Directory', 'recycle_bin/']:
                      if href.endswith('/'):
                          if browse:
                              addDir(name,url+href,15,icon,fanart,'','','')
                          else:
                              addDir(name,url+href,14,icon,fanart,'','','')
                      elif href.endswith('.xml'):
                          if browse:
                              addDir(name,url+href,1,icon,fanart,'','','','','download')
                          else:
                              addDir(name,url+href,11,icon,fanart,'','','','','download')
        except:
          addon_log('no XML links found')

def getSoup(url):
        if url.startswith('https://'):
            data = makeRequest(url)
        else:
            if xbmcvfs.exists(url):
                if url.startswith("smb://") or url.startswith("nfs://"):
                    copy = xbmcvfs.copy(url, os.path.join(profile, 'temp', 'sorce_temp.txt'))
                    if copy:
                        data = open(os.path.join(profile, 'temp', 'sorce_temp.txt'), "r").read()
                        xbmcvfs.delete(os.path.join(profile, 'temp', 'sorce_temp.txt'))
                    else:
                        addon_log("failed to copy from smb:")
                else:
                    data = open(url, 'r').read()
            else:
                addon_log("Soup Data not found!")
                return
        return BeautifulSOAP(data, convertEntities=BeautifulStoneSoup.XML_ENTITIES)


def getData(url,fanart):
        soup = getSoup(url)
        addon_log('No Channels: getItems')
        getItems(soup('item'),fanart)


def getItems(items,fanart):
        total = len(items)
        addon_log('Total Items: %s' %total)
        for item in items:
            try:
                name = item('title')[0].string
                if name is None:
                    name = 'unknown?'
            except:
                addon_log('Name Error')
                name = ''
            try:
                url = []
                for i in item('link'):
                    if not i.string == None:
                        url.append(i.string)
                if len(url) < 1:
                    raise
            except:
                addon_log('Error <link> element, Passing:'+name.encode('utf-8', 'ignore'))
                continue

            try:
                thumbnail = item('thumbnail')[0].string
                if thumbnail == None:
                    raise
            except:
                thumbnail = ''
            try:
                if not item('fanart'):
                    if addon.getSetting('use_thumb') == "true":
                        fanArt = thumbnail
                    else:
                        fanArt = fanart
                else:
                    fanArt = item('fanart')[0].string
                if fanArt == None:
                    raise
            except:
                fanArt = fanart
            try:
                desc = item('epgdata')[0].string
                desc = desc.replace('/NL/', '\n')
                if desc == None:
                    raise
            except:
                desc = 'No Games Scheduled'
            try:
                genre = item('genre')[0].string
                if genre == None:
                    raise
            except:
                genre = 'Sport'

            try:
                date = item('date')[0].string
                if date == None:
                    raise
            except:
                date = '2016'

            try:
                if len(url) > 1:
                    alt = 0
                    playlist = []
                    for i in url:
                        playlist.append(i)
                    if addon.getSetting('add_playlist') == "false":
                        for i in url:
                            alt += 1
                            addLink(i,'%s) %s' %(alt, name.encode('utf-8', 'ignore')),thumbnail,fanArt,desc,genre,date,True,playlist,regexs,total)
                    else:
                        addLink('', name.encode('utf-8', 'ignore'),thumbnail,fanArt,desc,genre,date,True,playlist,regexs,total)
                else:
                    addLink(url[0],name.encode('utf-8', 'ignore'),thumbnail,fanArt,desc,genre,date,True,None,regexs,total)
            except:
                addon_log('There was a problem adding item - '+name.encode('utf-8', 'ignore'))


def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                splitparams={}
                splitparams=pairsofparams[i].split('=')
                if (len(splitparams))==2:
                    param[splitparams[0]]=splitparams[1]
        return param

def play_playlist(name, list):
        playlist = xbmc.PlayList(1)
        playlist.clear()
        item = 0
        for i in list:
            item += 1
            info = xbmcgui.ListItem('%s) %s' %(str(item),name))
            playlist.add(i, info)
        xbmc.executebuiltin('playlist.playoffset(video,0)')


def addDir(name,url,mode,iconimage,fanart,description,genre,date,credits,showcontext=False):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&fanart="+urllib.quote_plus(fanart)
        ok=True
        if date == '':
            date = None
        else:
            description += '\n\nDate: %s' %date
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo(type="Video", infoLabels={ "Title": name, "Plot": description, "Genre": genre, "dateadded": date, "credits": credits })
        liz.setProperty("Fanart_Image", fanart)
        if showcontext:
            contextMenu = []
            if showcontext == 'download':
                contextMenu.append(('Download','XBMC.RunPlugin(%s?url=%s&mode=9&name=%s)'
                                    %(sys.argv[0], urllib.quote_plus(url), urllib.quote_plus(name))))
            liz.addContextMenuItems(contextMenu)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok


def addLink(url,name,iconimage,fanart,description,genre,date,showcontext,playlist,regexs,total):
        try:
            name = name.encode('utf-8')
        except: pass
        ok = True
        if regexs: mode = '17'
        else: mode = '12'
        u=sys.argv[0]+"?"
        play_list = False
        if playlist:
            if addon.getSetting('add_playlist') == "false":
                u += "url="+urllib.quote_plus(url)+"&mode="+mode
            else:
                u += "mode=13&name=%s&playlist=%s" %(urllib.quote_plus(name), urllib.quote_plus(str(playlist).replace(',','|')))
                play_list = True
        else:
            u += "url="+urllib.quote_plus(url)+"&mode="+mode
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo(type="Video", infoLabels={ "Title": name, "Plot": description, "Genre": genre, "dateadded": date })
        liz.setProperty("Fanart_Image", fanart)
        if not play_list:
            liz.setProperty('IsPlayable', 'true')
        if showcontext:
            contextMenu = []
            fav_params = (
                '%s?mode=5&name=%s&url=%s&iconimage=%s&fanart=%s&fav_mode=0'
                %(sys.argv[0], urllib.quote_plus(name), urllib.quote_plus(url), urllib.quote_plus(iconimage), urllib.quote_plus(fanart))
                )
            if playlist:
                fav_params += 'playlist='+urllib.quote_plus(str(playlist).replace(',','|'))
            if regexs:
                fav_params += "&regexs="+regexs
            contextMenu.append(('Add to LiveStreams Favorites','XBMC.RunPlugin(%s)' %fav_params))
            liz.addContextMenuItems(contextMenu)
        if not playlist is None:
            if addon.getSetting('add_playlist') == "false":
                playlist_name = name.split(') ')[1]
                contextMenu_ = [
                    ('Play '+playlist_name+' PlayList','XBMC.RunPlugin(%s?mode=13&name=%s&playlist=%s)'
                     %(sys.argv[0], urllib.quote_plus(playlist_name), urllib.quote_plus(str(playlist).replace(',','|'))))
                     ]
                liz.addContextMenuItems(contextMenu_)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=total)
        return ok

def getADauth():

        URL_LOGIN = 'https://gonna.mobi/amember/login'

        http_header = {
                        'Host' : 'gonna.mobi',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
                        'Accept' : '*/*',
                        'Accept-Language' : 'en-GB,en;q=0.5',
                        'Accept-Encoding' : 'gzip, deflate',
                        'Content-Type' : 'application/x-www-form-urlencoded; charset=UTF-8',
                        'X-Requested-With' : 'XMLHttpRequest',
                        'Referer' : 'https://gonna.mobi/amember/login'
                        }

        params = {
          'amember_login' : PADLuser,
          'amember_pass': PADLpass
        }
        
        req = urllib2.Request(URL_LOGIN, urllib.urlencode(params), http_header)
        page = urllib2.urlopen(req);
        response=page.read();
        page.close()
        successMsg = re.search('"ok":true', response)
        if successMsg is None:
          addon_log("login failure")
          return 'Error'
        else:
          addon_log("login successful")
        cookie=page.info()['Set-Cookie']
        addon.setSetting('cookieDetails', cookie)
        return cookie
        
        
def getHash(cookie):

        URL_AUTH = 'https://gonna.mobi/premium/wp/epg/?hash=on'
        try:
          req = urllib2.Request(URL_AUTH)#send the new url with the cookie.
          req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0')
          req.add_header('Cookie',cookie)
          page = urllib2.urlopen(req)
        except urllib2.HTTPError, ex:
          return 'Error'
        response=page.read();
        page.close()
        errorMsg = re.search('Please login', response)
        if errorMsg is not None:
          return 'Error'
        if response.endswith('='):
          cleanResult = response
        else:
          cleanResult = response+'='
        decodedHash = base64.b64decode(cleanResult)
        addon_log("decoded hash is "+decodedHash)
        if decodedHash.startswith('server_time='):
          return response
        else:
          return 'Error'
        
def detailsPrompt():
      xbmcgui.Dialog().ok('Error', "Problem logging in", "Check Username and Password")
      addon.openSettings()
      xbmc.executebuiltin("XBMC.Container.Update(path,replace)")
      xbmc.executebuiltin("XBMC.ActivateWindow(Videos,addons://sources/video)")
      
xbmcplugin.setContent(int(sys.argv[1]), 'movies')

try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
except:
    pass
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
except:
    pass
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
except:
    pass
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_GENRE)
except:
    pass

params=get_params()

url=None
name=None
mode=None
playlist=None
iconimage=None
fanart=FANART
playlist=None
fav_mode=None
regexs=None


try:
    url=urllib.unquote_plus(params["url"]).decode('utf-8')
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    iconimage=urllib.unquote_plus(params["iconimage"])
except:
    pass
try:
    fanart=urllib.unquote_plus(params["fanart"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass
try:
    playlist=eval(urllib.unquote_plus(params["playlist"]).replace('|',','))
except:
    pass
try:
    fav_mode=int(params["fav_mode"])
except:
    pass
try:
    regexs=params["regexs"]
except:
    pass

addon_log("Mode: "+str(mode))
if not url is None:
    addon_log("URL: "+str(url.encode('utf-8')))
addon_log("Name: "+str(name))

addon_log("Checking username and password have been set")

if PADLuser == '':detailsPrompt()
if PADLuser == None:detailsPrompt()

if PADLpass == '':detailsPrompt()
if PADLpass == None:detailsPrompt()

addon_log("Checking cookie is set and valid")

if cookieDetails == '':getADauth()
if cookieDetails == None:getADauth()

if cookieDetails == 'Error':detailsPrompt()

addon_log("Cookie retrieved - "+cookieDetails)

addon_log("Checking hash can be retrieved")

getHashCode = getHash(cookieDetails)

if getHashCode == 'Error':
  addon_log("error retrieving hash - trying to login again")
  retryEffort = getADauth()
  if retryEffort == 'Error':
    addon_log("failed to login - asking for username and password")
    detailsPrompt()
  else:
    getHashCode = getHash(retryEffort)
    addon_log("hash retrieved - "+getHashCode)
    cookieDetails = addon.getSetting('cookieDetails')
    addon_log("new cookie is - "+cookieDetails)

finalHash = getHashCode


if mode==None:
    addon_log("Getting XML links from PLAD")
    get_xml_database(PLADDir, cookieDetails, True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==1:
    addon_log("getData")
    getData(url,fanart)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==11:
    addon_log("addSource")
    addSource(url)

elif mode==12:
    addon_log("playing URL - "+url)
    item = xbmcgui.ListItem(path=url+PLADVar+finalHash)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

elif mode==13:
    addon_log("play_playlist")
    play_playlist(name, playlist)

elif mode==14:
    addon_log("get_xml_database")
    get_xml_database(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==15:
    addon_log("browse_xml_database")
    get_xml_database(url, cookieDetails, True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))