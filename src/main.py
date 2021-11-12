import sys
sys.path.insert(0, "./youtube-dl")
import youtube_dl
import http.server
import socketserver
from urllib.parse import urlparse
from urllib.parse import parse_qs

# MyHttpRequestHandler
#
# Handle server requests.
class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler) :
  # do_GET()
  #
  # Handle GET requests from clients.
  def do_GET(self) :
    self.send_response(200)
    # Extract query param
    video = "NONE"
    html = "<h1>error</h1>"
    query_components = parse_qs(urlparse(self.path).query)
    if "v" in query_components :
      video = query_components["v"][0]
    # TODO: Pull the HTML out of the configuration file.
    path = self.path.split("/", 2)[1]
    print(path) # TODO
    # Check what we should do
    if path == "" :
      self.send_header("Content-type", "text/html")
      html = f"""
<html>
  <head>
    <title>ytoff</title>
  </head>
  <body bgcolor="#000" text="#FFF"><center><tt>
      <h1>ytoff</h1>
      <p>
        <i>Watch Youtube videos offline.</i>
      </p>
  </tt></center></body>
</html>"""
    elif path == "raw" :
      # TODO: Check the file exists.
      self.send_header("Content-type", "video/mp4")
      with open(f"../raw/{video}.mp4", "rb") as file :
        self.wfile.write(file.read())
    else :
      self.send_header("Content-type", "text/html")
      html = f"""
<html>
  <head>
    <title>ytoff</title>
  </head>
  <body bgcolor="#000" text="#FFF"><center><tt>
      <h1>ytoff</h1>
      <p>
        [<a href="/?v={video}">this</a>]
        [<a href="https://www.youtube.com/watch?v={video}">youtube</a>]
      </p>
      <p>
        <video width="560" height="315" controls>
          <source src="raw/{video}.mp4?v={video}" type="video/mp4">
          Your browser does not support the video tag.
        </video>
      </p>
  </tt></center></body>
</html>"""
    self.end_headers()
    # Writing the HTML contents with UTF-8
    self.wfile.write(bytes(html, "utf8"))
    return

# yt_download()
#
# Download a video with the given parameters.
#
# @param video The video code to be downloaded.
def yt_download(video) :
  # TODO: Check that the video code is sane and not dangerous.
  ydl_opts = {
    'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]'
  }
  with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download([f"https://youtube.com/watch?v={video}"])
  return

# main()
#
# The main entry point into the program.
def main() :
  # Setup the server
  handler = MyHttpRequestHandler
  port = 8080 # TODO: Move to configuration file.
  server = socketserver.TCPServer(("", port), handler)
  # Run the server
  server.serve_forever()
  return

if __name__ == "__main__" :
  main()
