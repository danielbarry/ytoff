#!/bin/bash

root="$(pwd)"

# Remove old video files
cd raw
  for f in *.jpg *.mp4 *.part; do
    rm "./$f"
  done
cd $root

# Run the main program
cd src
  python3 main.py
cd $root
