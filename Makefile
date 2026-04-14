# itsUP - Development and deployment automation
# Usage: make <target>

.PHONY: help up down restart logs build pull clean dev status

# Default target
.DEFAULT_GOAL := help

# Load environment variables
ifneq (,$(wildcard .env))
	include .env
	export
endif

COMPOSE_FILE ?= docker-compose.yml
DOCKER_COMPOSE := docker compose -f $(COMPOSE_FILE)

## help: Show this help message
help:
	@echo "itsUP - Available commands:"
	@echo ""
	@sed -n 's/^## //p' $(MAKEFILE_LIST) | column -t -s ':' | sed -e 's/^/ /'
	@echo ""

## up: Start all services in detached mode
up:
	$(DOCKER_COMPOSE) up -d --remove-orphans

## down: Stop and remove all services
down:
	$(DOCKER_COMPOSE) down

## restart: Restart all services
restart:
	$(DOCKER_COMPOSE) restart

## logs: Follow logs for all services (use SERVICE=<name> to filter)
logs:
	$(DOCKER_COMPOSE) logs -f --tail=200 $(SERVICE)

## build: Build or rebuild services
build:
	$(DOCKER_COMPOSE) build --pull

## pull: Pull latest images
pull:
	$(DOCKER_COMPOSE) pull

## clean: Stop services and remove volumes
clean:
	$(DOCKER_COMPOSE) down -v --remove-orphans

## dev: Start services with live reload (development mode)
dev:
	$(DOCKER_COMPOSE) up

## status: Show status of all services
status:
	$(DOCKER_COMPOSE) ps

## config: Validate and view the docker-compose configuration
config:
	$(DOCKER_COMPOSE) config

## setup: Copy sample env file if .env does not exist
setup:
	@if [ ! -f .env ]; then \
		cp .env.sample .env; \
		echo ".env created from .env.sample — please edit it before starting."; \
	else \
		echo ".env already exists, skipping."; \
	fi

## update: Pull latest images and recreate containers
update: pull
	$(DOCKER_COMPOSE) up -d --remove-orphans
