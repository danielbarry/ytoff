import os
import sys
import json
sys.path.insert(0, "./youtube-dl")
import youtube_dl
import http.server
import socketserver
from urllib.parse import urlparse
from urllib.parse import parse_qs

config = json.loads("{}")

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
      html = ""
      if os.path.exists(f"../raw/{video}.mp4") :
        self.send_header("Content-type", config["response"]["video"]["content"])
        for s in config["response"]["video"]["html"] :
          html += s
      else :
        yt_download(video)
        self.send_header("Content-type", config["response"]["process"]["content"])
        for s in config["response"]["process"]["html"] :
          html += s
    self.end_headers()
    # Writing the HTML contents with UTF-8
    html = html.format(
      title = config["decoration"]["title"],
      bgcolor = config["decoration"]["bgcolor"],
      fgcolor = config["decoration"]["fgcolor"],
      code = video
    )
    self.wfile.write(bytes(html, "utf8"))
    return

# yt_download()
#
# Download a video with the given parameters.
#
# @param video The video code to be downloaded.
def yt_download(video) :
  # TODO: Check that the video code is sane and not dangerous.
  with youtube_dl.YoutubeDL(config["youtube-dl"]["options"]) as ydl:
    ydl.download([f"https://youtube.com/watch?v={video}"])
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
  # Run the server
  server.serve_forever()
  return

if __name__ == "__main__" :
  main()
