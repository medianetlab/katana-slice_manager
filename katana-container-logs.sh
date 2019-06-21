#!/bin/bash

# Get the logs from the katana manager 
file=katana-container-logs
if [[ -L "$file" ]]; then
    rm -f $file
fi
container_logs1=$(docker inspect --format='{{.LogPath}}' katanamngr_katana_1)
container_logs2=$(docker inspect --format='{{.LogPath}}' katana-mngr_katana_1)
if [[ $container_logs1 ]]; then
	ln -s $container_logs2 $file
	tail -f $file
	rm -f $file
elif [[ $container_logs2 ]]; then
	ln -s $container_logs2 $file
	tail -f $file
	rm -f $file
else
	echo "Log files are redirected to a remote log server"
fi

