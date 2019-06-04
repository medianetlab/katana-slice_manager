
# DOCKER TASKS

katana-build: ## Build the image
	docker image build -t katana .

katana-build-nc: ## Build the image without caching
	docker image build --no-cache -t katana .

katana-run: ## Run container
	docker container run -i -t --rm --name katana-container -p 8000:8000 --mount type=bind,src=$(shell pwd),dst=/katana katana

katana-stop: ## Stop a running container
	docker container stop katana-container

katana-rm: ## Remove a stopped container
	docker container rm katana-container


# DOCKER-COMPOSE TASKS

up:
	docker-compose up

down:
	docker-compose down

up-build:
	docker-compose up --build

build-no-cache:
	docker-compose build --no-cache

start:
	docker-compose start

stop:
	docker-compose stop