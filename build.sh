#!/bin/bash

root="$(pwd)"

cd src/yt-dlp
  make clean
  make
cd $root
