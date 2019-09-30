#!/bin/bash

# Get the logs from the katana manager 
file=katana-container-logs
if [[ -L "$file" ]]; then
    rm -f $file
fi
container_logs=$(docker inspect --format='{{.LogPath}}' katana-mngr)
if [[ $container_logs ]]; then
	ln -s $container_logs $file
	tail -f $file
	rm -f $file
else
	echo "Log files are redirected to a remote log server"
fi

