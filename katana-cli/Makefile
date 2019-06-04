
# DOCKER TASKS

build: ## Build the image
	docker image build -t katana-cli .

build-nc: ## Build the image without caching
	docker image build --no-cache -t katana-cli .

run: ## Run container
	docker container run -d -it --net=host --name katana-cli-container --mount type=bind,src=$(shell pwd)/cli,dst=/katana-cli/cli katana-cli


up: build run


stop: ## Stop a running container
	docker container stop katana-cli-container

rm: ## Remove a stopped container
	docker container rm katana-cli-container

down: stop rm
