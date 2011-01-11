from PMS import Plugin, Log, DB, Thread, XML, HTTP, JSON, RSS, Utils
from PMS.MediaXML import MediaContainer, DirectoryItem, TrackItem, SearchDirectoryItem
from PMS.Shorthand import _L, _R, _E, _D
from lxml import etree

PLUGIN_PREFIX  = "/music/NPR"
NPR_ROOT       = 'http://api.npr.org'
API_KEY        = 'MDAyNTU3MTA2MDEyMjk2NTE1MzEwN2U0MQ001'
LIST_URL       = NPR_ROOT + '/list?apiKey=' + API_KEY
QUERY_URL      = NPR_ROOT + '/query?numResults=20&apiKey=' + API_KEY
SEARCH_URL     = NPR_ROOT + '/query?startNum=0&sort=dateDesc&output=NPRML&numResults=20&apiKey=' + API_KEY
CACHE_INTERVAL = 600

def _UE(str):
  return _E(str.encode('utf8'))

dirs = [ ['Topics', '3002'], 
         ['Music Genres', '3018'], 
         ['Programs' , '3004'],
         ['Bios' , '3007'],
         ['Music Artists' , 'music'],
         ['Columns' , '3003'],
         ['Series' , '3006'] ]
         
musicDirs = [ ['Recent Artists', '3008'],
              ['All Artists', '3009'] ]

####################################################################################################
def Start():
  Plugin.AddRequestHandler(PLUGIN_PREFIX, HandleAudioRequest, "National Public Radio", "icon-default.jpg", "art-default.png")
  Plugin.AddViewGroup("Details", viewMode="InfoList", contentType="items")

####################################################################################################
def _S(item, attr): 
  try:
    return item.find(attr).text.replace('<em>','').replace('</em>','').replace('&mdash;','-')
  except:
    return ''

####################################################################################################
def ParseStories(dir, url):
  dir.SetAttr('filelabel', '%T')
  trackIndex = 1
  for item in XML.ElementFromString(HTTP.GetCached(url, CACHE_INTERVAL)).xpath('//story'):
    try: duration = int(item.find('audio').find('duration').text)*1000
    except: duration = ''
    
    try:
      mp3 = item.xpath('audio/format/mp3')[0].text
      track = TrackItem(PLUGIN_PREFIX+'/media/'+_E(mp3)+'.mp3', _S(item,'title'), 'National Public Radio', _S(item,'slug'), str(trackIndex), '', str(duration), '', _R('icon-default.jpg'))
      track.SetAttr('summary', _S(item,'teaser'))
      track.SetAttr('totalTime', str(duration))
      track.SetAttr('subtitle', ' '.join(_S(item,'storyDate').split()[0:4]))
      dir.AppendItem(track)
      trackIndex += 1
    except:
      pass
    
####################################################################################################
def HandleAudioRequest(pathNouns, count):
  
  if count == 0:
    dir = MediaContainer('art-default.png')
    for (n,v) in dirs:
      dir.AppendItem(DirectoryItem(v+"$"+n, n, ""))
    dir.AppendItem(SearchDirectoryItem("search", "Search...", "Search NPR", _R("search.png")))
    
  elif count > 1 and pathNouns[0] == 'search':
    dir = MediaContainer('art-default.png', 'Details', "NPR", "Search: " + ' '.join(pathNouns[1:]))
    url = SEARCH_URL + '&searchTerm=' + '%20'.join(pathNouns[1:])
    ParseStories(dir, url)
    
  elif count == 2 and pathNouns[0] == 'media':
    mp3 = HTTP.GetCached(_D(pathNouns[1].split('.')[0]), CACHE_INTERVAL)
    mp3 = mp3.split('\n')[0]
    return Plugin.Redirect(mp3)
    
  elif count == 1 and pathNouns[0].startswith('music'):
    dir = MediaContainer('art-default.png', None, "NPR", "Music Artists")
    for (n,v) in musicDirs:
      dir.AppendItem(DirectoryItem(PLUGIN_PREFIX+'/'+v+"$"+n, n, _R('icon-default.jpg')))
  
  elif count == 1:
    (id,title) = pathNouns[0].split('$')
    dir = MediaContainer('art-default.png', 'Details', "NPR", title)
    maxNumToReturn = 5
    for item in XML.ElementFromString(HTTP.GetCached(LIST_URL + '&id=' + id, CACHE_INTERVAL)).xpath('//item'):
      dir.AppendItem(DirectoryItem('story/'+item.get('id')+'$'+_E(title)+'$'+_UE(_S(item,'title')), 
                     _S(item,'title'), _R('icon-default.jpg'), _S(item,'additionalInfo')))
      if id == '3008':
        maxNumToReturn -= 1
        if maxNumToReturn <= 0: 
          break
      
  elif count == 3:
    (id,title,title2) = pathNouns[2].split('$')
    dir = MediaContainer('art-default.png', 'Details', _D(title), _D(title2))
    ParseStories(dir, QUERY_URL + '&id=' + id)

  return dir.ToXML()