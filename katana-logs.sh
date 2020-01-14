#!/bin/bash

# file-katana-mngr/katana.log
# tail -f $file

printf "\n%s\n%s\n%s\n" "+----------------------------+" "|      katana-mngr logs      |" "+----------------------------+"
docker logs katana-mngr

printf "\n%s\n%s\n%s\n" "+---------------------------+" "|      katana-nbi logs      |" "+---------------------------+"
docker logs katana-nbi

printf "\n%s\n%s\n%s\n" "+---------------------------+" "|      katana-cli logs      |" "+---------------------------+"
docker logs katana-cli
