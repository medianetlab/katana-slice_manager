#!/bin/bash


containers="mongo zookeeper kafka katana-nbi katana-mngr katana-cli katana-swagger"

# Check for help option
if [[ " $* " =~ " -h " ]] || [[ " $* " =~ " --help " ]];
then
     printf "Usage:\n\tstart.sh [-p | --publish] [-r | --release <RELEASE_NUMBER>] [-g | --graphical-ui] [-m | --monitoring] [-h | --help]\nOptions:
        \t[-p | --publish] : Expose Kafka end Swagger-ui using katana public IP
        \t[-r | --release <RELEASE_NUMBER>] : Specify the release version to be deployed (default is latest)
        \t[-g | --graphical-ui] : Start Web User Interface
        \t[-m | --monitoring] : Start the monitoring module
        \t[-h | --help] : Print this message and quit\n"
        exit 0
fi

export KATANA_VERSION="latest"

# Get the options
while [[ $# -gt 0 ]]
do
    key=$1

    case $key in
    -p | --publish)
        read -r -p "Expose Kafka Message Bus and Swagger-ui? (Y/n) " ans

        if [[ $ans != "n" ]];
        then
            message="katana host public IP"
            ip_list=$(hostname -I 2> /dev/null)
            if (( $? == 0 ));
            then
                message="${message} (Available: $ip_list)"
            fi
            read -r -p "${message} >> " HOST_IP
            export "DOCKER_HOST_IP=${HOST_IP}"

            # Insert Katana's IP in swagger conf file
            sed -i "s?katanaSM?${HOST_IP}?" ./swagger/swagger.json
        fi
        shift
    ;;
    -g | --graphical-ui)
        containers="${containers} postgres katana-ui"
        gui=true
        shift
    ;;
    -m | --monitoring)
        containers="${containers} katana-prometheus katana-grafana katana-nfv_mon"
        # Check if katana-grafana/.env file exists - If not create it
        if [ ! -f ./katana-grafana/.env ];
        then
        echo "GF_SECURITY_ADMIN_PASSWORD=admin" > katana-grafana/.env
        echo "GF_SECURITY_ADMIN_USER=admin" >> katana-grafana/.env
        fi
        sed -i 's/KATANA_MONITORING=.*/KATANA_MONITORING=True/' katana-mngr/.env
        shift
    ;;
    -r | --release)
        export KATANA_VERSION=$2
        shift
        shift
    ;;
    *)
    printf "Wrong option %s\n--------\n" "${key}"
    printf "Usage:\n\tstart.sh [-p | --publish] [-r | --release <RELEASE_NUMBER>] [-g | --graphical-ui] [-m | --monitoring] [-h | --help]\nOptions:
    \t[-p | --publish] : Expose Kafka end Swagger-ui using katana public IP
    \t[-r | --release <RELEASE_NUMBER>] : Specify the release version to be deployed (default is latest)
    \t[-g | --graphical-ui] : Start Web User Interface
    \t[-m | --monitoring] : Start the monitoring module
    \t[-h | --help] : Print this message and quit\n"
    exit 9999
    ;;
    esac
done

# Install the command for the cli tool to /usr/local/bin/
command -v katana &> /dev/null || cp katana /usr/local/bin/

# Start the docker containers on the background
docker-compose up -d ${containers}

if [ "$gui" = true ];
then
    docker exec -it katana-ui ui db init
    docker exec -it katana-ui ui db seed
fi