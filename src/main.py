import os
import time
import sys
import threading
import json
import base64
sys.path.insert(0, "./yt-dlp")
import yt_dlp as youtube_dl
import http.server
import socketserver
from urllib.parse import urlparse
from urllib.parse import parse_qs

config = json.loads("{}")
raw_loc = ""
fmt_dat = ""
fmt_img = ""
fmt_vid = ""
queue = []
dequeue = []

# valid_id()
#
# Check whether a given Youtube ID is valid (or at least not dangerous).
#
# @param The video to be checked.
# @return True if not harmful, otherwise false.
def valid_id(video) :
  if len(video) < 2 or len(video) > 64 :
   return False
  try:
    return str(
        base64.urlsafe_b64encode(
          base64.urlsafe_b64decode(video + "===")
        ).decode()
      ).replace("=", "") == video
  except Exception:
    return False

# ThreadingServer
#
# Multi-threaded server implementation.
class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
  pass

# RequestHandler
#
# Handle server requests.
class RequestHandler(http.server.BaseHTTPRequestHandler) :
  # do_GET()
  #
  # Handle GET requests from clients.
  #
  # @param self A reference to this object.
  def do_GET(self) :
    try :
      self.send_response(200)
      # Extract query param
      video = "NONE"
      html = ""
      for s in config["response"]["error"]["html"] :
        html += s
      query_components = parse_qs(urlparse(self.path).query)
      if "v" in query_components :
        video = query_components["v"][0]
      if not valid_id(video) :
        print("[!!] Invalid ID given")
        return
      path = self.path.split("/", 2)[1]
      # Check what we should do
      if path == "" :
        self.send_header("Content-type", config["response"]["home"]["content"])
        html = ""
        for s in config["response"]["home"]["html"] :
          html += s
      elif path == "raw" :
        self.send_header("Content-type", config["response"]["raw"]["content"])
        self.end_headers()
        with open(f"{raw_loc}/{video}.{fmt_vid}", "rb") as file :
          self.wfile.write(file.read())
        return
      elif path == "thumb" :
        self.send_header("Content-type", config["response"]["thumb"]["content"])
        self.end_headers()
        with open(f"{raw_loc}/{video}.{fmt_img}", "rb") as file :
          self.wfile.write(file.read())
        return
      else :
        if os.path.exists(f"{raw_loc}/{video}.{fmt_vid}") :
          html = ""
          self.send_header("Content-type", config["response"]["video"]["content"])
          for s in config["response"]["video"]["html"] :
            html += s
        else :
          # Only append videos if the queue not overloaded
          if len(queue) < config["youtube-dl"]["max-queue"] :
            # Don't double add videos
            if video != "NONE" and not video in queue :
              queue.append(video)
            html = ""
            self.send_header("Content-type", config["response"]["process"]["content"])
            for s in config["response"]["process"]["html"] :
              html += s
      self.end_headers()
      # Try to load video configuration
      vdata = {
        "title": "Unkown",
        "channel": "Unknown",
        "channel_url": "https://youtube.com",
        "upload_date": "yyyymmdd",
        "description": "Unknown"
      }
      if os.path.exists(f"{raw_loc}/{video}.{fmt_dat}") :
        with open(f"{raw_loc}/{video}.{fmt_dat}", "r") as f :
          data = f.read()
        vdata = json.loads(data)
      # Writing the HTML contents with UTF-8
      html = html.format(
        title = config["decoration"]["title"],
        vtitle = vdata["title"],
        vchannel = vdata["channel"],
        vchannelurl = vdata["channel_url"],
        vupload = vdata["upload_date"][0:4] + "-" + vdata["upload_date"][4:6] + "-" + vdata["upload_date"][6:8],
        vdesc = vdata["description"].replace("\n", "<br>"),
        logo = config["decoration"]["logo"],
        bgcolor = config["decoration"]["bgcolor"],
        fgcolor = config["decoration"]["fgcolor"],
        width = config["decoration"]["width"],
        height = config["decoration"]["height"],
        img = fmt_img,
        vid = fmt_vid,
        code = video,
        lenq = len(queue),
        wait = config["response"]["process"]["wait-time-ms"]
      )
      self.wfile.write(bytes(html, "utf8"))
    except Exception as exception :
      print("[!!] Client thread crashed: {} -> {}".format(type(exception).__name__, exception))
    return

# service_loop()
#
# Download videos in the queue to the target directory and remove old videos to
# save on space.
def service_loop() :
  while True :
    try :
      # Check if we want to remove something old
      if len(dequeue) > config["youtube-dl"]["max-dequeue"] :
        video = dequeue[0]
        dequeue.remove(video)
        if os.path.exists(f"{raw_loc}/{video}.{fmt_dat}") :
          os.remove(f"{raw_loc}/{video}.{fmt_dat}")
        if os.path.exists(f"{raw_loc}/{video}.{fmt_img}") :
          os.remove(f"{raw_loc}/{video}.{fmt_img}")
        if os.path.exists(f"{raw_loc}/{video}.{fmt_vid}") :
          os.remove(f"{raw_loc}/{video}.{fmt_vid}")
      # Check if we want to download something new
      if len(queue) > 0 :
        video = queue[0]
        # Check if ID is somewhat valid
        if valid_id(video) :
          # Blocking download
          with youtube_dl.YoutubeDL(config["youtube-dl"]["options"]) as ydl :
            obj = ydl.extract_info(f"https://youtube.com/watch?v={video}", download=False)
            with open(f"{raw_loc}/{video}.{fmt_dat}", "w") as f :
              json.dump(obj, f)
            ydl.download([f"https://youtube.com/watch?v={video}"])
          dequeue.append(video)
        queue.remove(video)
      time.sleep(15)
    except Exception as exception :
      print("[!!] Service thread crashed: {} -> {}".format(type(exception).__name__, exception))
  return

# main()
#
# The main entry point into the program.
def main() :
  global config, raw_loc, fmt_dat, fmt_img, fmt_vid
  # Read configuration
  with open("../default.json", "r") as f :
    data = f.read()
  config = json.loads(data)
  raw_loc = config["disk"]["raw-loc"]
  fmt_dat = config["youtube-dl"]["formats"]["data"]
  fmt_img = config["youtube-dl"]["formats"]["image"]
  fmt_vid = config["youtube-dl"]["formats"]["video"]
  # Setup the server
  handler = RequestHandler
  server = ThreadingServer(("", config["server"]["port"]), handler)
  # Run the downloader thread
  dt = threading.Thread(target = service_loop)
  dt.start()
  # Run the server thread
  st = threading.Thread(target = server.serve_forever)
  st.start()
  # Finally, join our threads (we should never get here)
  dt.join()
  st.join()
  return

if __name__ == "__main__" :
  main()
