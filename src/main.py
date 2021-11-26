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
from functools import partial

config = json.loads("{}")
raw_loc = ""
fmt_dat = ""
fmt_img = ""
fmt_vid = ""
yt_url = ""
pre_html = ""
post_html = ""
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

# log_action()
#
# Log an action being taken.
#
# @param sub The subject of the action.
# @param act The action performed.
def log_action(sub, act) :
  print("[>>] {} -> {}".format(
    sub, act
  ))
  return

# log_exception()
#
# Produce a nicely formatted exception.
#
# @param e The exception to be printed.
def log_exception(e) :
  print("[!!] Service thread crashed: {}::{} -> {}".format(
    type(e).__name__, sys.exc_info()[2].tb_lineno, e
  ))
  return

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
        html += s + "\n"
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
          html += s + "\n"
      elif path == "raw" :
        self.send_header("Content-type", config["response"]["raw"]["content"])
        self.end_headers()
        if os.path.exists(f"{raw_loc}/{video}.{fmt_vid}") :
          with open(f"{raw_loc}/{video}.{fmt_vid}", "rb") as file :
            for chunk in iter(partial(file.read, config["server"]["chunk-size"]), b"") :
              self.wfile.write(chunk)
        return
      elif path == "thumb" :
        self.send_header("Content-type", config["response"]["thumb"]["content"])
        self.end_headers()
        if os.path.exists(f"{raw_loc}/{video}.{fmt_img}") :
          with open(f"{raw_loc}/{video}.{fmt_img}", "rb") as file :
            for chunk in iter(partial(file.read, config["server"]["chunk-size"]), b"") :
              self.wfile.write(chunk)
        return
      else :
        if os.path.exists(f"{raw_loc}/{video}.{fmt_vid}") :
          html = ""
          self.send_header("Content-type", config["response"]["video"]["content"])
          for s in config["response"]["video"]["html"] :
            html += s + "\n"
        else :
          # Only append videos if the queue not overloaded
          if len(queue) < config["youtube-dl"]["max-queue"] :
            # Don't double add videos
            if video != "NONE" and not video in queue :
              queue.append(video)
              log_action("queue", "appended " + video)
            html = ""
            self.send_header("Content-type", config["response"]["process"]["content"])
            for s in config["response"]["process"]["html"] :
              html += s + "\n"
          else :
            html = ""
            for s in config["response"]["error-busy"]["html"] :
              html += s + "\n"
      self.end_headers()
      # Try to load video configuration
      vdata = {
        "title": "Unkown",
        "channel": "Unknown",
        "channel_url": f"{yt_url}",
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
        wait = config["response"]["process"]["wait-time-ms"],
        yturl = yt_url,
        prehtml = pre_html.format(
          title = config["decoration"]["title"],
          vtitle = vdata["title"],
        ),
        posthtml = post_html,
      )
      self.wfile.write(bytes(html, "utf8"))
    except Exception as exception :
      log_exception(exception)
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
        log_action("dequeue", "removing " + video + " of age " + str(oldest))
        if os.path.exists(f"{raw_loc}/{video}.{fmt_dat}") :
          os.remove(f"{raw_loc}/{video}.{fmt_dat}")
        if os.path.exists(f"{raw_loc}/{video}.{fmt_img}") :
          os.remove(f"{raw_loc}/{video}.{fmt_img}")
        if os.path.exists(f"{raw_loc}/{video}.{fmt_vid}") :
          os.remove(f"{raw_loc}/{video}.{fmt_vid}")
      # Check if we want to download something new
      if len(queue) > 0 :
        video = queue[0]
        # Update queue immediately to prevent infinite loop
        queue.remove(video)
        # Don't double add videos and deplete the cache
        if not video in dequeue :
          dequeue.append(video)
        log_action("dequeue", "appended " + video)
        # Check if ID is somewhat valid
        if valid_id(video) :
          log_action("youtube-dl", "downloading " + video)
          # Blocking download
          with youtube_dl.YoutubeDL(config["youtube-dl"]["options"]) as ydl :
            obj = ydl.extract_info(f"{yt_url}/watch?v={video}", download=False)
            with open(f"{raw_loc}/{video}.{fmt_dat}", "w") as f :
              json.dump(obj, f)
            ydl.download([f"{yt_url}/watch?v={video}"])
      time.sleep(15)
    except Exception as exception :
      log_exception(exception)
  return

# main()
#
# The main entry point into the program.
def main() :
  global config, raw_loc, fmt_dat, fmt_img, fmt_vid, yt_url, pre_html, post_html
  log_action("server", "starting")
  # Read configuration
  with open("../default.json", "r") as f :
    data = f.read()
  config = json.loads(data)
  raw_loc = config["disk"]["raw-loc"]
  fmt_dat = config["youtube-dl"]["formats"]["data"]
  fmt_img = config["youtube-dl"]["formats"]["image"]
  fmt_vid = config["youtube-dl"]["formats"]["video"]
  yt_url = config["youtube-dl"]["url"]
  for s in config["response"]["default"]["pre-html"] :
    pre_html += s + "\n"
  for s in config["response"]["default"]["post-html"] :
    post_html += s + "\n"
  # Setup the server
  handler = RequestHandler
  server = ThreadingServer(("", config["server"]["port"]), handler)
  # Run the downloader thread
  dt = threading.Thread(target = service_loop)
  log_action("thread_service", "starting")
  dt.start()
  # Run the server thread
  st = threading.Thread(target = server.serve_forever)
  log_action("thread_server", "starting")
  st.start()
  # Finally, join our threads (we should never get here)
  dt.join()
  st.join()
  log_action("server", "ended")
  return

if __name__ == "__main__" :
  main()
