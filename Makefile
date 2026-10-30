
# These can be overridden with environment variables or command-line variables.
REGISTRY ?= cluster-registry:5000
IMAGE_NAME ?= customers
IMAGE_TAG ?= 1.0
IMAGE ?= $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
PLATFORM ?= "linux/amd64,linux/arm64"
CLUSTER ?= nyu-devops
KUBECTL_CONTEXT ?= k3d-$(CLUSTER)
INGRESS_PORT ?= 8080
INGRESS_URL ?= http://127.0.0.1:$(INGRESS_PORT)

.SILENT:

.PHONY: help
help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: all
all: help

##@ Development

.PHONY: clean
clean: ## Remove dangling build cache and the current image.
	$(info Removing dangling build cache...)
	-docker rmi $(IMAGE)
	docker image prune -f
	docker buildx prune -f

.PHONY: install
install: ## Install Python dependencies.
	$(info Installing dependencies...)
	sudo pipenv install --system --dev

.PHONY: lint
lint: ## Run the linter.
	$(info Running linting...)
	-flake8 service tests --count --select=E9,F63,F7,F82 --show-source --statistics
	-flake8 service tests --count --max-complexity=10 --max-line-length=127 --statistics
	-pylint service tests --max-line-length=127

.PHONY: test
test: ## Run the unit tests.
	$(info Running tests...)
	export RETRY_COUNT=1; pytest --pspec --cov=service --cov-fail-under=95 --disable-warnings

.PHONY: run
run: ## Run the service.
	$(info Starting service...)
	honcho start

.PHONY: secret
secret: ## Generate a new secret hex key.
	python3 -c 'import secrets; print(secrets.token_hex())'

##@ Kubernetes

.PHONY: cluster
cluster: ## Create a k3d cluster with a local registry and load balancer.
	$(info Creating Kubernetes cluster $(CLUSTER) with one worker node...)
	k3d cluster create $(CLUSTER) --agents 1 --registry-create cluster-registry:5000 --registry-config ./config/registries.yaml --port '$(INGRESS_PORT):80@loadbalancer'

.PHONY: cluster-rm
cluster-rm: ## Remove the configured k3d cluster.
	$(info Removing Kubernetes cluster $(CLUSTER)...)
	k3d cluster delete $(CLUSTER)

.PHONY: import
import: ## Import the image into the configured k3d cluster.
	$(info Importing $(IMAGE) into k3d cluster $(CLUSTER)...)
	k3d image import --cluster $(CLUSTER) $(IMAGE)

.PHONY: deploy
deploy: ## Deploy PostgreSQL, the service, and ingress; then verify them.
	$(info Checking Kubernetes context $(KUBECTL_CONTEXT)...)
	kubectl --context="$(KUBECTL_CONTEXT)" cluster-info >/dev/null
	$(info Deploying PostgreSQL...)
	kubectl --context="$(KUBECTL_CONTEXT)" apply -f k8s/postgres/
	kubectl --context="$(KUBECTL_CONTEXT)" rollout status statefulset/customers-db --timeout=180s
	$(info Deploying Customers application, Service, and Ingress...)
	kubectl --context="$(KUBECTL_CONTEXT)" apply -f k8s/deployment.yaml -f k8s/service.yaml -f k8s/ingress.yaml
	kubectl --context="$(KUBECTL_CONTEXT)" rollout status deployment/customers --timeout=180s
	$(MAKE) verify

.PHONY: verify
verify: ## Verify application health and database access through ingress.
	$(info Checking application health through ingress...)
	curl --fail --silent --show-error --retry 10 --retry-connrefused --retry-delay 2 --max-time 10 $(INGRESS_URL)/health
	@echo
	$(info Checking the database-backed Customers endpoint through ingress...)
	curl --fail --silent --show-error --retry 10 --retry-connrefused --retry-delay 2 --max-time 10 $(INGRESS_URL)/customers
	@echo

############################################################
# COMMANDS FOR BUILDING THE IMAGE
############################################################

##@ Image Build and Push

.PHONY: init
init: export DOCKER_BUILDKIT=1
init: ## Create the buildx instance.
	$(info Initializing Builder...)
	-docker buildx create --use --name=qemu
	docker buildx inspect --bootstrap

.PHONY: build
build: ## Build the project container image for the local platform.
	$(info Building $(IMAGE)...)
	docker build --rm --pull --tag $(IMAGE) .

.PHONY: push
push: ## Push the image to the container registry.
	$(info Pushing $(IMAGE)...)
	docker push $(IMAGE)

.PHONY: buildx
buildx: ## Build and push a multi-platform image.
	$(info Building multi-platform image $(IMAGE) for $(PLATFORM)...)
	docker buildx build --file Dockerfile --pull --platform=$(PLATFORM) --tag $(IMAGE) --push .

.PHONY: remove
remove: ## Stop and remove the buildx builder.
	$(info Stopping and removing the buildx builder...)
	docker buildx stop
	docker buildx rm
