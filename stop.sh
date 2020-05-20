#!/bin/bash

# Check for help option
if [[ " $@ " =~ " -h " ]] || [[ " $@ " =~ " --help " ]];
then
    printf "Usage:\n\tstart.sh [-c | --clear] [-h | --help]\nOptions:
    \t[-c | --clear] : Remove the container volumes
    \t[-h | --help] : Print this message and quit\n"
    exit 0
fi

# Get the options
while [[ $# -gt 0 ]]
do
    key=$1
    case $key in
    -c | --clear)
        options="$options -v"
        shift
    ;;
    *)
    printf "Wrong option ${key}\n--------\n"
    printf "Usage:\n\tstart.sh [-c | --clear] [-h | --help]\nOptions:
    \t[-c | --clear] : Remove the container volumes
    \t[-h | --help] : Print this message and quit\n"
    exit 0
    ;;
    esac
done

# Stop the containers
docker-compose down $options

# Remove the katana-container-log file
file=katana-container-logs
if [[ -L "$file" ]]; then
    rm -f $file
fi

# Remove the katana-log files
file1=katana-nbi/katana.log*
file2=katana-mngr/katana.log*
rm -f $file1 $file2
