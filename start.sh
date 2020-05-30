#!/bin/bash


containers="mongo zookeeper kafka katana-nbi katana-mngr katana-cli swagger"

# Check for help option
if [[ " $* " =~ " -h " ]] || [[ " $* " =~ " --help " ]];
then
     printf "Usage:\n\tstart.sh [-p | --publish] [-g | --graphical-ui] [-h | --help]\nOptions:
        \t[-p | --publish] : Expose Kafka end Swagger-ui using katana public IP
        \t[-g | --graphical-ui] : Start Web User Interface
        \t[-h | --help] : Print this message and quit\n"
        exit 0
fi

# Get the options
while [[ $# -gt 0 ]]
do
    key=$1

    case $key in
    -p | --publish)
        read -r -p "Expose Kafka Message Bus and Swagger-ui? (Y/n) " ans

        if [[ $ans != "n" ]];
        then
            read -r -p "katana host public IP > " HOST_IP
            export "DOCKER_HOST_IP=${HOST_IP}"

            # Insert Katana's IP in swagger conf file
            sed -i "s?katanaSM?${HOST_IP}?" ./swagger/swagger.json
        fi
        shift
    ;;
    -g | --graphical-ui)
        containers=""
        gui=true
        shift
    ;;
    *)
    printf "Wrong option %s\n--------\n" "${key}"
    printf "Usage:\n\tstart.sh [-p | --publish] [-g | --graphical-ui] [-h | --help]\nOptions:
    \t[-p | --publish] : Expose Kafka end Swagger-ui using katana public IP
    \t[-g | --graphical-ui] : Start Web User Interface
    \t[-h | --help] : Print this message and quit\n"
    exit 9999
    ;;
    esac
done

# Start the docker containers on the background
docker-compose up -d ${containers}

if [ "$gui" = true ];
then
    docker exec -it katana-ui ui db init
    docker exec -it katana-ui ui db seed
fi