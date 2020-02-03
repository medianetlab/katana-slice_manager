# Katana Slice Manager

![](./katana-ui/ui/static/images/katana-logo.svg)

----------

Network slicing is a 5G cutting edge technology, that enables the creation of multiple virtual networks on top of a physical architecture, allowing operators to provide portions of their networks that fit with the requirementsby different vertical industries. A network slice can be described as the sum of various sub-slices of different network domains, such as the WAN, the Core Cloud and the Edge Cloud. 

Katana Slice Manager is a central software component responsible for controlling all the devices comprising the network, providing an interface for creating, modifying, monitoring and deleting slices. Through the NBI, Katana interacts with a coordination layer or directly with the network operator. It receives the Network Slice Template (NEST) for creating network slices and provides the API for managing and monitoring them. Through the South Bound Interface (SBI), it talks to the components of the Management and Orchestration Layer (MANO), namely the NFV Orchestrator (NFVO), the Virtual Infrastructure Manager (VIM), the Element Management System (EMS) and the WAN Infrastructure Management (WIM), in order to manage the functions in the network and perform CRUD operations on End-to-End network slices.

Katana Slice Manager is based on a highly modular architecture, built as a mess of microservices, each of whom is running on a docker container. The key advantages of this architectural approach are that it offers simplicity in building and maintaining applications, flexibility and scalability, while the containerized approach makes the applications independent of the underlying system.

## Quick Start

### Requirements
- docker version >= 18.09.6
- docker-compose version >= 1.17.1

### Installation
````
# ./install.sh
````

### Start
Start katana Slice Manager service without the web UI module, run:
````
# ./start.sh
````

Start katana Slice Manager service and the web UI module, run:
````
# ./start-ui.sh
````

### Stop
Stop Katana service, but keep the databases with any associated data:
````
# ./stop.sh
````

Stop Katana service, and clean any associated data:
````
# ./clear.sh
````
## Documentation
- [Wiki](https://github.com/medianetlab/katana-slice_manager/wiki)
- [5GENESIS Deliverable](https://5genesis.eu/wp-content/uploads/2019/10/5GENESIS_D3.3_v1.0.pdf)