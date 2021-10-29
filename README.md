# Katana Slice Manager

![Katana Logo](./templates/images/katana-logo.svg)

----------

[![Stargazers](https://img.shields.io/github/stars/medianetlab/katana-slice_manager?style=for-the-badge)](https://github.com/medianetlab/katana-slice_manager/stargazers)
[![Forks](https://img.shields.io/github/forks/medianetlab/katana-slice_manager?style=for-the-badge)](https://github.com/medianetlab/katana-slice_manager/network/members)
[![Commit Activity](https://img.shields.io/github/commit-activity/m/medianetlab/katana-slice_manager?style=for-the-badge)](https://github.com/medianetlab/katana-slice_manager/graphs/commit-activity)

[![Watchers](https://img.shields.io/github/watchers/medianetlab/katana-slice_manager?style=for-the-badge)](https://github.com/medianetlab/katana-slice_manager/watchers)
[![Contributors](https://img.shields.io/github/contributors/medianetlab/katana-slice_manager?style=for-the-badge)](https://github.com/medianetlab/katana-slice_manager/graphs/contributors)
[![Issues](https://img.shields.io/github/issues/medianetlab/katana-slice_manager?style=for-the-badge)](https://github.com/medianetlab/katana-slice_manager/issues)

[![Build Status](https://jenkins.medianetlab.gr/buildStatus/icon?job=katana%2Fmnl.testing)](https://jenkins.medianetlab.gr/job/katana/job/mnl.testing/)

----------

Network slicing is a 5G cutting edge technology, that enables the creation of multiple virtual networks on top of a physical architecture, allowing operators to provide portions of their networks that fit with the requirementsby different vertical industries. A network slice can be described as the sum of various sub-slices of different network domains, such as the WAN, the Core Cloud and the Edge Cloud.

Katana Slice Manager is a central software component responsible for controlling all the devices comprising the network, providing an interface for creating, modifying, monitoring and deleting slices. Through the NBI, Katana interacts with a coordination layer or directly with the network operator. It receives the Network Slice Template (NEST) for creating network slices and provides the API for managing and monitoring them. Through the South Bound Interface (SBI), it talks to the components of the Management and Orchestration Layer (MANO), namely the NFV Orchestrator (NFVO), the Virtual Infrastructure Manager (VIM), the Element Management System (EMS) and the WAN Infrastructure Management (WIM), in order to manage the functions in the network and perform CRUD operations on End-to-End network slices.

Katana Slice Manager is based on a highly modular architecture, built as a mesh of microservices, each of which is running on a docker container. The key advantages of this architectural approach are that it offers simplicity in building and maintaining applications, flexibility and scalability, while the containerized approach makes the applications independent of the underlying system.

## Features

- Start, Stop, Inspect End-to-End Network Slices
- OpenAPIs supported by Swagger-io tool
- Modular architecture for supporting different infrastructure technologies
- Integrated CLI tool
- Prometheus and Grafana Monitoring modules
- Slice Deployment and Configuration measurements
- CI/CD procedures

## Quick Start

### :chains: Requirements

- docker version >= 18.09.6
- docker-compose version >= 1.17.1

### :hammer_and_pick: Build

Build the Katana Docker images and install the katana CLI command on the local system.

``` bash
bash bin/build.sh [-r | --release <RELEASE_NUMBER>] [--docker_reg <REMOTE_DOCKER_REGISTRY>] [--docker_repo <DOCKER_REPOSITORY>] [--docker_reg_user <REGISTRY_USER>] [--docker_reg_passwd <REGISTRY_PASSWORD>] [--push] [--dev] [-h | --help]
```

Options:

- __[-r | --release <RELEASE_NUMBER>] :__ Define the release that will match the Docker Tag of Katana Docker images (Default: :test).
- __[--docker_reg <REMOTE_DOCKER_REGISTRY>] :__ Define the remote Docker registry. If no docker registry is specified, Katana will try to use the public Docker hub
- __[--docker_repo <DOCKER_REPOSITORY>] :__ Define the Docker repository
- __[--docker_reg_user <REGISTRY_USER>] :__ Define the user of the remote Docker registry
- __[--docker_reg_passwd <REGISTRY_PASSWORD>] :__ Define the password for the user of the remote Docker registry
- __[--push] :__ Push the images to the remote Docker registry
- __[--dev] :__ Create a dev workspace for development purposes
- __[-h | --help] :__ Print this message and quit

> Sudo privileges will be needed for installing the CLI command tool

### :gear: Deploy

Deploy katana Slice Manager service. The script will attempt to pull the defined Docker tag from the defined Docker registry/repository. Otherwise, it will build the images using the ":test" tag.

``` bash
bash bin/deploy.sh [-p | --publish] [-r | --release <RELEASE_NUMBER>] [--docker_reg <REMOTE_DOCKER_REGISTRY>] [--docker_repo <DOCKER_REPOSITORY>] [--docker_reg_user <REGISTRY_USER>] [--docker_reg_passwd <REGISTRY_PASSWORD>] [-m | --monitoring] [-h | --help]
```

Options:

- __[-p | --publish] :__ Expose Kafka end Swagger-ui using katana public IP
- __[-r | --release <RELEASE_NUMBER>] :__ Define the release that will match the Docker Tag of Katana Docker images (Default: :test).
- __[--docker_reg <REMOTE_DOCKER_REGISTRY>] :__ Define the remote Docker registry. If no docker registry is specified, Katana will try to use the public Docker hub
- __[--docker_repo <DOCKER_REPOSITORY>] :__ Define the Docker repository
- __[--docker_reg_user <REGISTRY_USER>] :__ Define the user of the remote Docker registry
- __[--docker_reg_passwd <REGISTRY_PASSWORD>] :__ Define the password for the user of the remote Docker registry
- __[-m | --monitoring] :__ Start Katana Slice Manager Slice Monitoring module
- __[--no_build] :__ Try to download Docker images, but do not build them
- __[-h | --help] :__ Print help message and quit

### :clipboard: Logs

Get the logs of katana-mngr and katana-nbi modules:

```bash
katana logs [-l | --limit N]
```

- __-l | --limit__: Show limited number of lines from the end of the logs (default "all")

### :stop_button: Stop

Stop Katana Slice Manager:

```bash
bash bin/stop.sh [-c | --clear] [-h | --help]
```

- __[-c | --clear] :__ Remove the container volumes
- __[-h | --help] :__ Print help message and quit

### :wastebasket: Uninstall

Remove katana Docker resources and the CLI command tool

```bash
bash bin/uninstall.sh
```

> Sudo privileges will be needed for removing the CLI command tool

### :chart_with_upwards_trend: Monitoring

To start Prometheus and Grafana Monitoring modules add the `-m | --monitoring` flag to `./start.sh` binary. Prometheus is running at port __9090__ and Grafana at port __3000__. A new dashboard will be created on Grafana for every new slice that is created.

By default Grafana credentials are admin:admin. To change it, create the `katana-grafana/.env` file with the following environmental variables:

```bash
GF_SECURITY_ADMIN_USER=USER
GF_SECURITY_ADMIN_PASSWORD=PASSWORD
```

## Development Environment

To create a development environment for katana on a Linux host, run:

```bash
./build.sh --dev
```

This will create hard links of the __shared_utils__ directory of both katana-mngr and katana-nbi on the root directory `./dev_shared_utils`. So any changes done on the existing files ./shared_utils directory will be reflected to __katana-mngr/katana/shared_utils__ and __katana-nbi/katana/shared_utils__ directories. To add new files that are created in the dev_shared_utils directory, run the command:

```bash
for dest in katana-{mngr,nbi}/katana/shared_utils/; do cp -al dev_shared_utils/{PATH_TO_NEW_FILE} $dest; done
```

It will also create a **dev** folder, where the example_config_files will be copied for a more direct access to testing configuration files

You can also check the [Wiki "For Developers"](https://github.com/medianetlab/katana-slice_manager/wiki/developers) page for more details.

## CI/CD

Current implementation supports two pipelines, using the respective Jenkinsfile:

- Multibranch Pipeline using the file `Jenkinsfile`:

  - Builds the docker images if there was a change on the code
  - Runns the Integration test
  - If the changes are occuring on the master branch, the built images will be packaged and uploaded to docker hub
  - Sends notification on Slack

- Pipeline for tagging using the file `jenkins/tag/Jenkinsfile`. For every new tag:
  - Builds the docker images using as tag the git push tag
  - Runns the Integration test
  - The built images will be packaged and uploaded to docker hub
  - Sends notification on Slack

The two Jenkins jobs can be created using a seed DSL job and the script `jenkins/Jenkins_Seed_DSL_Jobs/jobs`

## Documentation

- [Wiki](https://github.com/medianetlab/katana-slice_manager/wiki)
- [5GENESIS Deliverable](https://5genesis.eu/wp-content/uploads/2019/10/5GENESIS_D3.3_v1.0.pdf)
