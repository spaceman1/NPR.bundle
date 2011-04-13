PLUGIN_PREFIX  = "/music/NPR"
NPR_ROOT       = 'http://api.npr.org'
API_KEY        = 'MDAyNTU3MTA2MDEyMjk2NTE1MzEwN2U0MQ001'
LIST_URL       = NPR_ROOT + '/list?apiKey=' + API_KEY
QUERY_URL      = NPR_ROOT + '/query?numResults=20&apiKey=' + API_KEY
SEARCH_URL     = NPR_ROOT + '/query?startNum=0&sort=dateDesc&output=NPRML&numResults=20&apiKey=' + API_KEY
CACHE_INTERVAL = 600

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
	Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, "National Public Radio", "icon-default.jpg", "art-default.png")
	Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
	MediaContainer.art = R('art-default.jpg')
	DirectoryItem.thumb = R('icon-default.jpg')

####################################################################################################

def S(item, attr): 
	try:
		return item.find(attr).text.replace('<em>','').replace('</em>','').replace('&mdash;','-')
	except:
		return ''

####################################################################################################

def ParseStories(dir, url):
#	dir.SetAttr('filelabel', '%T')
	trackIndex = 1
	for item in XML.ElementFromURL(url, cacheTime=CACHE_INTERVAL).xpath('//story'):
		try: duration = int(item.find('audio').find('duration').text) * 1000
		except: duration = None
		
		try:
			mp3 = item.xpath('audio/format/mp3')[0].text
			
			dir.Append(Function(TrackItem(PlayMusic, title=S(item,'title'), artist=S(item, 'slug'), duration=duration, summary=S(item,'teaser'), subtitle=' '.join(S(item,'storyDate').split()[0:4])), url=mp3))
			trackIndex += 1
		except IndexError:
			pass
	
####################################################################################################

def MainMenu():
	dir = MediaContainer()
	for name, value in dirs:
		if value == 'music':
			dir.Append(Function(DirectoryItem(MusicMenu, title=name)))
		else:
			dir.Append(Function(DirectoryItem(SectionMenu, title=name), id=value))
	dir.Append(Function(InputDirectoryItem(Search, title="Search...", prompt="Search NPR", thumb=R("search.png"))))
	return dir

def MusicMenu(sender):
	dir = MediaContainer(title2="Music Artists")
	for name, value in musicDirs:
		dir.Append(Function(DirectoryItem(SectionMenu, title=name), id=value))
	return dir

def Search(sender, query):
	dir = MediaContainer(viewGroup='Details', title2="Search: " + query)
	url = SEARCH_URL + '&searchTerm=' + query.replace(' ', '%20')
	ParseStories(dir, url)
	return dir

def PlayMusic(sender, url):
	target = HTTP.Request(url, cacheTime=CACHE_INTERVAL).content.split('\n')[0]
	Log(target)
	return Redirect(target)
	
def SectionMenu(sender, id):
	dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
	maxNumToReturn = 200
	for item in XML.ElementFromURL(LIST_URL + '&id=' + id, cacheTime=CACHE_INTERVAL).xpath('//item'):
		dir.Append(Function(DirectoryItem(StoryMenu, title=S(item,'title'), thumb=R('icon-default.jpg'), summary=S(item,'additionalInfo')), id=item.get('id')))
		if id == '3008':
			maxNumToReturn = maxNumToReturn - 1
			if maxNumToReturn <= 0: 
				break
	return dir

def StoryMenu(sender, id):
	dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
	ParseStories(dir, QUERY_URL + '&id=' + id)
	if len(dir) == 0:
		return MessageContainer('No Audio', 'No audio files were found in this section.')
	return dir