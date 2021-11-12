**ytoff**

*Watch Youtube videos offline.*

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
