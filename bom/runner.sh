#!/bin/bash

# get the directory path of the bash file
bash_dir=$(dirname "$0")

# change the current working directory to the bash file directory
cd "$bash_dir" || exit

docker build -t bom_downloader ./
docker run -it --rm -v /data/bom_radar:/app/data/bom_radar bom_downloader