#!/bin/bash


containers="mongo zookeeper kafka katana-nbi katana-mngr katana-cli swagger"

# Check for help option
if [[ " $* " =~ " -h " ]] || [[ " $* " =~ " --help " ]];
then
     printf "Usage:\n\tstart.sh [-p | --publish] [-g | --graphical-ui] [-m | --monitoring] [-h | --help]\nOptions:
        \t[-p | --publish] : Expose Kafka end Swagger-ui using katana public IP
        \t[-g | --graphical-ui] : Start Web User Interface
        \t[-m | --monitoring] : Start the monitoring module
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
        containers="${containers} katana-prometheus katana-grafana"
        # Check if katana-grafana/.env file exists - If not create it
        if [ ! -f ./katana-grafana/.env ];
        then
        echo "GF_SECURITY_ADMIN_PASSWORD=admin" > katana-grafana/.env
        echo "GF_SECURITY_ADMIN_USER=admin" >> katana-grafana/.env
        fi
        shift
    ;;
    *)
    printf "Wrong option %s\n--------\n" "${key}"
    printf "Usage:\n\tstart.sh [-p | --publish] [-g | --graphical-ui] [-m | --monitoring] [-h | --help]\nOptions:
    \t[-p | --publish] : Expose Kafka end Swagger-ui using katana public IP
    \t[-g | --graphical-ui] : Start Web User Interface
    \t[-m | --monitoring] : Start the monitoring module
    \t[-h | --help] : Print this message and quit\n"
    exit 9999
    ;;
    esac
done

# Start the docker containers on the background
echo docker-compose up -d ${containers}
exit 0
if [ "$gui" = true ];
then
    docker exec -it katana-ui ui db init
    docker exec -it katana-ui ui db seed
fi