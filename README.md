# katana Slice Manager version 2.0.0

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
