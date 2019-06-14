#!/bin/bash

# Get the logs from the katana manager 
file=katana-logs
if [[ -L "$file" ]]; then
    rm -f $file
fi
ln -s $(docker inspect --format='{{.LogPath}}' katanamngr_katana_1) $file
tail -f $file
rm -f $file
