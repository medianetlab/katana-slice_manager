#!/bin/bash

# Get the logs from the katana manager 
file=katana-logs
if [[ -L "$file" ]]; then
    rm -f $file
fi
container_logs=$(docker inspect --format='{{.LogPath}}' katanamngr_katana_1)
if [[ $container_logs ]]; then
	ln -s $(docker inspect --format='{{.LogPath}}' katanamngr_katana_1) $file
	tail -f $file
	rm -f $file
else
	echo "Log files are redirected to a remote log server"
fi

