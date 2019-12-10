LANG  := C
CYAN  := \033[36m
GREEN := \033[32m
RESET := \033[0m

# http://postd.cc/auto-documented-makefile/
.DEFAULT_GOAL := help
.PHONY: help
help: ## Show this help
	@grep -hE '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "${CYAN}%-30s${RESET} %s\n", $$1, $$2}'

.PHONY: lint-nofix
lint-nofix: ## Check lint
	@poetry run black --target-version py36 --check .
	@poetry run isort -c -rc .
	@poetry run autoflake -r --check --remove-all-unused-imports --remove-unused-variables .

.PHONY: lint
lint: ## Check lint and fix
	@poetry run black --target-version py36 .
	@poetry run isort -y --atomic -rc .
	@poetry run autoflake -r --in-place --remove-all-unused-imports --remove-unused-variables .

.PHONY: type
type:	## Check types
	@poetry run mypy .
