import sys
import dbus
import pypresence
import time
import logging

from config import *

class PresenceUpdate:
	def __init__(self):
		logging.basicConfig(stream=sys.stdout, level=logging.INFO)
		self.logger = logging.getLogger(__name__)
		print("[INFO] Starting...")

		self.bus = dbus.SessionBus()
		self.client = pypresence.Presence(APPLICATION_ID)
		self.player = None
		self.prop_iface = None

	def run(self):
		while True:
			try:
				if not self.prop_iface:
					print("[INFO] Connecting to Clementine")
					self.player = self.bus.get_object("org.mpris.MediaPlayer2.clementine", '/org/mpris/MediaPlayer2')
					self.prop_iface = dbus.Interface(self.player, dbus_interface="org.freedesktop.DBus.Properties")
				print("[INFO] Connecting to Discord")
				self.client.connect()

				self.presence_loop()

			except dbus.exceptions.DBusException as e:
				print("[ERROR] Connection to Clementine failed : %s" %str(e))
				print("[INFO] Reconnecting in 5s")
				self.player = None
				self.prop_iface = None
				time.sleep(5)

			except (pypresence.exceptions.InvalidID) as e:
				print("[ERREUR] Connection to Discord failed : %s" % str(e))
				print("[INFO] Reconnecting in 5s")
				time.sleep(5)

	def presence_loop(self):
		print("[INFO] Reading data from Clementine and updating Discord Rich Presence statut")
		while True:
			try:
				metadata = self.prop_iface.Get(MPRIS_MP2, "Metadata")
				position = self.prop_iface.Get(MPRIS_MP2, "Position") / 1000000
				playback_statut = self.prop_iface.Get(MPRIS_MP2, "PlaybackStatus")
			except dbus.exceptions.DBusException as e:
				self.client.clear()
				raise e

			large_img = "clementine_logo"
			artist_music = None
			album_music = None

			start = None

			if playback_statut == "Stopped":
				small_image = "stop_circle"
				small_text = STOP_TXT
				details = STOP_DETAILS
				state = None
			else:
				temp_metadata = dict()
				for key, value in metadata.items():
					temp_metadata[key.replace(':', '-')] = value
				try:
					state = "{xesam-title}".format(**temp_metadata) + " " # Dirty hack to avoid crash when the title is less than 2 caracters
					artist_music = "{xesam-artist[0]}".format(**temp_metadata)
					album_music = "{xesam-album}".format(**temp_metadata)
				except KeyError:
					pass

				if artist_music and album_music:
					details = artist_music + ": " + album_music
				elif artist_music:
					details = artist_music
				elif album_music:
					details = NO_ARTIST + album_music
				elif not artist_music and not album_music:
					details = NO_ARTIST_NOR_ALBUM

			if playback_statut == "Paused":
				small_image = "pause_circle"
				small_text = PAUSE_TXT

			if playback_statut == "Playing":
				small_image = "play_circle"
				small_text = PLAY_TXT
				try:
					time_now = time.time()
					start = time_now - position
				except KeyError:
					pass

			self.client.update(large_image=large_img,
						       small_image=small_image,
							   small_text=small_text,
							   large_text=LARGE_TXT,
							   details=details,
							   state=state,
							   start=start)

			time.sleep(1)

if __name__ == "__main__":
	updater = PresenceUpdate()
	updater.run()
	
