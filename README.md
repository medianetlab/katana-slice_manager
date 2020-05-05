# Katana Slice Manager

![Katana Logo](./katana-ui/ui/static/images/katana-logo.svg)

----------

Network slicing is a 5G cutting edge technology, that enables the creation of multiple virtual networks on top of a physical architecture, allowing operators to provide portions of their networks that fit with the requirementsby different vertical industries. A network slice can be described as the sum of various sub-slices of different network domains, such as the WAN, the Core Cloud and the Edge Cloud.

Katana Slice Manager is a central software component responsible for controlling all the devices comprising the network, providing an interface for creating, modifying, monitoring and deleting slices. Through the NBI, Katana interacts with a coordination layer or directly with the network operator. It receives the Network Slice Template (NEST) for creating network slices and provides the API for managing and monitoring them. Through the South Bound Interface (SBI), it talks to the components of the Management and Orchestration Layer (MANO), namely the NFV Orchestrator (NFVO), the Virtual Infrastructure Manager (VIM), the Element Management System (EMS) and the WAN Infrastructure Management (WIM), in order to manage the functions in the network and perform CRUD operations on End-to-End network slices.

Katana Slice Manager is based on a highly modular architecture, built as a mess of microservices, each of whom is running on a docker container. The key advantages of this architectural approach are that it offers simplicity in building and maintaining applications, flexibility and scalability, while the containerized approach makes the applications independent of the underlying system.

## Features

- Start, Stop. Inspect End-to-End Network SLices
- OpenAPIs supported by Swagger-io tool
- Modular architecture for supporting different infrastructure technologies
- Lightweight web UI
- Integrated CLI tool
- Slice Deployment and Configuration measurements

## Quick Start

### Requirements

- docker version >= 18.09.6
- docker-compose version >= 1.17.1

### Installation

```bash
sudo ./install.sh
```

### Start

Start katana Slice Manager service without the web UI module:

```bash
./start.sh
```

Start katana Slice Manager service and the web UI module:

```bash
./start-ui.sh
```

### Logs

Get the logs of katana-mngr and katana-nbi modules:

```bash
katana logs [-l | --limit N]
```

> limit option will show limited number of lines from the end of the logs (default "all")

### Stop

Stop Katana service, but keep the databases with any associated data:

```bash
./stop.sh
```

Stop Katana service, and clean any associated data:

```bash
sudo ./clear.sh
```

### Uninstall

Uninstall katana docker images and commands

```bash
sudo ./uninstall.sh
```

## Development Environment

To create a development environment for katana on a Linux host, run:

```bash
./install.sh --dev
```

This will create hard links of the __shared_utils__ directory of both katana-mngr and katana-nbi on the root directory `./dev_shared_utils`. So any changes done on the existing files ./shared_utils directory will be reflected to __katana-mngr/katana/shared_utils__ and __katana-nbi/katana/shared_utils__ directories. To add new files that are created in the dev_shared_utils directory, run the command:

```bash
for dest in katana-{mngr,nbi}/katana/shared_utils/; do cp -al dev_shared_utils/{PATH_TO_NEW_FILE} $dest; done
```

It will also create a **dev** folder, where the example_config_files will be copied for a more direct access to testing configuration files

You can also check the [Wiki "For Developers"](https://github.com/medianetlab/katana-slice_manager/wiki/developers) page for more details.

## Documentation

- [Wiki](https://github.com/medianetlab/katana-slice_manager/wiki)
- [5GENESIS Deliverable](https://5genesis.eu/wp-content/uploads/2019/10/5GENESIS_D3.3_v1.0.pdf)
