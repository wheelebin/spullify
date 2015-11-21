import threading
from queue import Queue
import time

import youtube_dl
from bs4 import BeautifulSoup
import requests


def download(video_key):
	print('http://www.youtube.com/watch?v=%s' % video_key)
	ydl_opts = {
	    'format': 'bestaudio/best',
	    'postprocessors': [{
	        'key': 'FFmpegExtractAudio',
	        'preferredcodec': 'mp3',
	        'preferredquality': '140',
	    }],
	}
	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
	    ydl.download(['http://www.youtube.com/watch?v=%s' % video_key])

def remove_punctuation(sentance):
	# Will replace all puncutation marks with a single space
	# Will Also replace all double/tripple spaces with a single space

	punctuation_marks = """. , : ; ! [ ] ( ) # { } - _ | ` ´ " ' / & < > ~ ^ ¨ * % $ @"""

	for mark in punctuation_marks.split(" "):
		sentance = sentance.replace(mark, " ")

		sentance = sentance.replace("  ", " ")
		sentance = sentance.replace("   ", " ")

	return sentance


def accuracy_test(spotify_title, youtube_title, accuracy_level):

	# Remove puncuation and capital letters
	spotify_title = remove_punctuation(spotify_title).lower()
	youtube_title = remove_punctuation(youtube_title).lower()

	# Split titles for itteration
	spotify_title_list = spotify_title.split(" ")
	youtube_title_list = youtube_title.split(" ")

	# If accuracy level is higher then amount of chars in title, lower it
	# This need to be fixed in order to make searches more accurate
	if len(spotify_title_list) < accuracy_level:
		accuracy_level = len(spotify_title) - 1

	# Compare the mount of matching strings between the two titles
	similar_word_count = 0
	for x in spotify_title_list:
		for y in youtube_title_list:
			if x == y:
				similar_word_count += 1

	# Will only return True if two or more strings are similar
	if similar_word_count < accuracy_level:
		return False
	else:
		return True

def get_spotify_playlist(uri):
	temp_tracks = []

	embed_format = "https://embed.spotify.com/?uri="
	r = requests.get(embed_format+uri)
	soup = BeautifulSoup(r.text)
	
	track_artists = soup.findAll("li", { "class" : "artist" })
	track_title = soup.findAll("li", { "class" : "track-title" })


	for n in range(0, len(track_title)):
		track = "%s:%s" % (track_artists[n].text, track_title[n].text)
		temp_tracks.append(track)

	return temp_tracks

def get_youtube_link(tracks):
	yt_search = "https://www.youtube.com/results?search_query="
	video_keys = []

	for track in tracks:
		track = track.replace(":"," ")
		
		r = requests.get(yt_search + track)
		soup = BeautifulSoup(r.text)
		item_section = soup.find("ol", {"class": "item-section"})
		items = item_section.findAll("div", {"class": "yt-lockup-tile"})

		view_count = 0
		video_key = ""

		videos = []

		for item in items:
			# SOMEWHERE IN HERE IS WHERE THE ACCUARCY CHECKER NEEDS TO GO
			# FORMAT FOR accuracy_test IS:
			# Spotify_title, Youtube_title, accuracy_level
			# I DONT WANT TO BREAK, I WANT TO PICK NEXT SONG

			item_title = item.find("a", {"class": "yt-uix-tile-link"})

			if accuracy_test(track, item_title.text, 4) == False:
				continue
			else:
				pass

			item_meta_info = item.find("ul", {"class": "yt-lockup-meta-info"})
			item_key = item.get('data-context-item-id')

			# Some items are not videos but playlists with no meta info which would crash script
			try:
				item_views = str(item_meta_info).split("<li>")[2].replace(u"\xa0", "").split(" ")[0]
				print("Video not accurate enough")
			except:
				pass

			item_views = int(item_views)

			if item_views > view_count:
				view_count = item_views
				video_key = item_key


		print(track, video_key)
		video_keys.append(video_key)

	# Will print all video keys collected
	for x in video_keys:
		print(x)

	return video_keys

	
	
# lock to serialize console output
lock = threading.Lock()

def do_work(item):
    time.sleep(1) # pretend to do some lengthy work.
    # Make sure the whole print completes or threads can mix up output in one line.
    with lock:
        print(threading.current_thread().name,item)

# The worker thread pulls an item from the queue and processes it
def worker():
    while True:
        item = q.get()
        download(item)
        q.task_done()




if __name__ == '__main__':
	uri = "spotify:user:tehdawg:playlist:7yblzr1UMec0P7xixy3GOY"
	tracks = get_spotify_playlist(uri)
	video_keys = get_youtube_link(tracks)

	# Create the queue and thread pool.
	q = Queue()
	for i in range(4):
	     t = threading.Thread(target=worker)
	     t.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
	     t.start()

	# stuff work items on the queue (in this case, just a number).
	start = time.perf_counter()
	for video_key in video_keys:
	    q.put(video_key)

	q.join()

