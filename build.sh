#!/bin/bash

root="$(pwd)"

cd src/youtube-dl
  make clean
  make
cd $root
