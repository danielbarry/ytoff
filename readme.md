![](src/logo.svg)**ytoff**

*Watch Youtube videos offline.*

![Example of a
[3Blue1Brown](https://www.youtube.com/channel/UCYO_jab_esuFRV4b17AJtAw)
[video](https://www.youtube.com/watch?v=F3Qixy-r_rQ)](doc/example.png)

This project is based on [yt-dlp](https://github.com/yt-dlp/yt-dlp) (a fork of
[youtube-dl](https://github.com/ytdl-org/youtube-dl)).

# Why?

There are a few reasons as to why you would rather use this service rather than
Youtube:

* *Privacy* - You may not particularly want Youtube to know what you are or are
not watching.
* *Lightweight* - Having even just a handful of Youtube tabs open can be very
heavy on RAM and CPU.
* *Distraction* - This service offers nothing but a video to be watched.

*Why not use Invidious?* I found that it was using tonnes of RAM and CPU, as
well as making tonnes of DNS requests. This can be run locally or on a server.
It is super simple and easily hacked on.

## Use Case

The following is the expected average use of this service:

1. User opens a Youtube video in a new browser tab.
2. An installed browser plug-in (left undefined) redirects the URL to this
service.
3. The service adds the video to a backlog and downloads it to be viewed.
4. The user views the video from this service, rather than Youtube.

# Building

This only needs to be run once in order to build the Youtube-dl library:

    bash build.sh

# Running

You can simply run:

    bash run.sh

By default, `default.json` serves at `http://127.0.0.1:3333`.

To use, simply replace `https://youtube.com/<video_stuff>` with
`http://127.0.0.1:3333/<video_stuff>`.

# Configuration

*ytoff* is highly configurable, with most settings being easily configured in
`default.json`. It is expected that for most people this will offer enough
configuration capability.

The video downloaded by default is 480 to save on disk space and bandwidth for
everybody involved. It also opts to download as `mp4` as this is the best
container format for many devices, especially as it is also typically H264
encoded.

If this is still not enough, checkout `src/main.py`. The configuration is
loaded in the `main()` function and the two main threads are started, the
server thread and the service thread:

* *Server thread* - This is where each client is handled and the immediate
response happens. Also see that if a video does not already exist, it is
added to the queue.
* *Service thread* - This is where the videos get downloaded (and old ones
deleted). A video is selected from the queue via FIFO, which then get added
to the dequeue list. Once too many videos exist, the oldest downloaded videos
are deleted to make space. (See the settings in `default.json`, specifically
in `youtube-dl` for adjusting resource usage.)
