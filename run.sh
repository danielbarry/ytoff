#!/bin/bash

root="$(pwd)"

# Remove old video files
cd raw
  for f in *.jpg *.json *.mp4 *.part *.webm *.webp; do
    rm "./$f"
  done
cd $root

# Run the main program
cd src
  python3 -OO -m compileall -f -j 0 -o 2 . yt-dlp/
  python3 main.py
cd $root
