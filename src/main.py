import os
import time
import sys
import threading
import json
sys.path.insert(0, "./youtube-dl")
import youtube_dl
import http.server
import socketserver
from urllib.parse import urlparse
from urllib.parse import parse_qs

config = json.loads("{}")
queue = []
dequeue = []

# MyHttpRequestHandler
#
# Handle server requests.
class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler) :
  # do_GET()
  #
  # Handle GET requests from clients.
  #
  # @param self A reference to this object.
  def do_GET(self) :
    self.send_response(200)
    # Extract query param
    video = "NONE"
    html = ""
    for s in config["response"]["error"]["html"] :
      html += s
    query_components = parse_qs(urlparse(self.path).query)
    if "v" in query_components :
      video = query_components["v"][0]
    path = self.path.split("/", 2)[1]
    # Check what we should do
    if path == "" :
      self.send_header("Content-type", config["response"]["home"]["content"])
      html = ""
      for s in config["response"]["home"]["html"] :
        html += s
    elif path == "raw" :
      self.send_header("Content-type", config["response"]["raw"]["content"])
      with open(f"../raw/{video}.mp4", "rb") as file :
        self.wfile.write(file.read())
    else :
      if os.path.exists(f"../raw/{video}.mp4") :
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
    # Writing the HTML contents with UTF-8
    html = html.format(
      title = config["decoration"]["title"],
      logo = config["decoration"]["logo"],
      bgcolor = config["decoration"]["bgcolor"],
      fgcolor = config["decoration"]["fgcolor"],
      code = video,
      lenq = len(queue)
    )
    self.wfile.write(bytes(html, "utf8"))
    return

# service_loop()
#
# Download videos in the queue to the target directory and remove old videos to
# save on space.
def service_loop() :
  while True :
    # Check if we want to remove something old
    if len(dequeue) > config["youtube-dl"]["max-dequeue"] :
      video = dequeue[0]
      dequeue.remove(video)
      if os.path.exists(f"../raw/{video}.mp4") :
        os.remove(f"../raw/{video}.mp4")
    # Check if we want to download something new
    if len(queue) > 0 :
      video = queue[0]
      # Check if ID is somewhat valid
      if len(video) > 2 and len(video) < 16 :
        # Blocking download
        with youtube_dl.YoutubeDL(config["youtube-dl"]["options"]) as ydl:
          ydl.download([f"https://youtube.com/watch?v={video}"])
        dequeue.append(video)
      queue.remove(video)
    time.sleep(15)
  return

# main()
#
# The main entry point into the program.
def main() :
  global config
  # Read configuration
  with open("../default.json", "r") as f:
    data = f.read()
  config = json.loads(data)
  # Setup the server
  handler = MyHttpRequestHandler
  port = config["port"]
  server = socketserver.TCPServer(("", port), handler)
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
