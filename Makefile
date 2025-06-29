# MiauBot Build System
# Supports cross-platform builds using Docker

# Configuration
BUILD_DIR := ./dist
PLATFORMS := linux-amd64 linux-arm64
VERSION := $(shell cat VERSION 2>/dev/null || echo "dev")
GIT_HASH := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
FULL_VERSION := $(VERSION)+$(GIT_HASH)
BUILD_TIME := $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")

# Docker settings
DOCKER_BUILDKIT := 1
DOCKERFILE := Dockerfile.build

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m

.PHONY: all build clean help test-build docker-check

# Default target
all: build

# Build all platforms
build: docker-check
	@echo "$(BLUE)🚀 Building MiauBot executables...$(NC)"
	@./build.sh build

# Build for specific platform
build-linux-amd64: docker-check
	@echo "$(BLUE)🐧 Building for Linux AMD64...$(NC)"
	@docker buildx build \
		--platform linux/amd64 \
		--file $(DOCKERFILE) \
		--target export \
		--output $(BUILD_DIR) \
		.
	@if [ -f "$(BUILD_DIR)/miaubot-linux-amd64" ]; then \
		chmod +x "$(BUILD_DIR)/miaubot-linux-amd64"; \
		echo "$(GREEN)✅ Built miaubot-linux-amd64$(NC)"; \
	else \
		mv "$(BUILD_DIR)/miaubot-linux-"* "$(BUILD_DIR)/miaubot-linux-amd64" 2>/dev/null || true; \
		chmod +x "$(BUILD_DIR)/miaubot-linux-amd64" 2>/dev/null || true; \
		echo "$(GREEN)✅ Built miaubot-linux-amd64$(NC)"; \
	fi

build-linux-arm64: docker-check
	@echo "$(BLUE)🔥 Building for Linux ARM64...$(NC)"
	@docker buildx build \
		--platform linux/arm64 \
		--file $(DOCKERFILE) \
		--target export \
		--output $(BUILD_DIR) \
		.
	@if [ -f "$(BUILD_DIR)/miaubot-linux-arm64" ]; then \
		chmod +x "$(BUILD_DIR)/miaubot-linux-arm64"; \
		echo "$(GREEN)✅ Built miaubot-linux-arm64$(NC)"; \
	else \
		mv "$(BUILD_DIR)/miaubot-linux-"* "$(BUILD_DIR)/miaubot-linux-arm64" 2>/dev/null || true; \
		chmod +x "$(BUILD_DIR)/miaubot-linux-arm64" 2>/dev/null || true; \
		echo "$(GREEN)✅ Built miaubot-linux-arm64$(NC)"; \
	fi

# Future targets for other platforms

build-windows-amd64: docker-check
	@echo "$(YELLOW)⚠️  Windows AMD64 support coming soon$(NC)"
	@exit 1

build-darwin-amd64: docker-check
	@echo "$(YELLOW)⚠️  macOS AMD64 support coming soon$(NC)"
	@exit 1

build-darwin-arm64: docker-check
	@echo "$(YELLOW)⚠️  macOS ARM64 support coming soon$(NC)"
	@exit 1

# Clean build artifacts
clean:
	@echo "$(BLUE)🧹 Cleaning build artifacts...$(NC)"
	@./build.sh clean

# Show build information
info:
	@echo "$(BLUE)🔍 Build Information:$(NC)"
	@echo "  Version: $(VERSION)"
	@echo "  Git Hash: $(GIT_HASH)"
	@echo "  Full Version: $(FULL_VERSION)"
	@echo "  Build Time: $(BUILD_TIME)"
	@echo "  Platforms: $(PLATFORMS)"
	@echo "  Build Directory: $(BUILD_DIR)"
	@./build.sh info

# Test the build system
test-build: build
	@echo "$(BLUE)🧪 Testing built executable...$(NC)"
	@if [ -f "$(BUILD_DIR)/miaubot-linux-amd64" ]; then \
		echo "$(GREEN)✅ Executable exists$(NC)"; \
		$(BUILD_DIR)/miaubot-linux-amd64 --help > /dev/null && \
		echo "$(GREEN)✅ Executable runs successfully$(NC)" || \
		echo "$(RED)❌ Executable test failed$(NC)"; \
	else \
		echo "$(RED)❌ Executable not found$(NC)"; \
		exit 1; \
	fi

# Quick test without full build
quick-test:
	@echo "$(BLUE)⚡ Quick test using Python directly...$(NC)"
	@uv run python miaubot.py --help > /dev/null && \
		echo "$(GREEN)✅ Python version works$(NC)" || \
		echo "$(RED)❌ Python version failed$(NC)"

# Check Docker availability
docker-check:
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "$(RED)❌ Docker is not installed$(NC)"; \
		echo "Please install Docker: https://docs.docker.com/get-docker/"; \
		exit 1; \
	fi
	@if ! docker info >/dev/null 2>&1; then \
		echo "$(RED)❌ Docker daemon is not running$(NC)"; \
		echo "Please start Docker daemon"; \
		exit 1; \
	fi

# Release build (future use)
release: clean build test-build
	@echo "$(GREEN)🎉 Release build completed!$(NC)"
	@echo "$(BLUE)📦 Artifacts:$(NC)"
	@ls -lah $(BUILD_DIR)/

# Development helpers
dev-setup:
	@echo "$(BLUE)⚙️  Setting up development environment...$(NC)"
	@uv sync
	@echo "$(GREEN)✅ Development environment ready$(NC)"

# Format code
format:
	@echo "$(BLUE)✨ Formatting code...$(NC)"
	@uv run ruff format src/
	@echo "$(GREEN)✅ Code formatted$(NC)"

# Lint code
lint:
	@echo "$(BLUE)🔍 Linting code...$(NC)"
	@uv run ruff check src/
	@echo "$(GREEN)✅ Code linted$(NC)"

# Run tests (when we add them)
test:
	@echo "$(BLUE)🧪 Running tests...$(NC)"
	@echo "$(YELLOW)⚠️  Tests not implemented yet$(NC)"

# Version management
version-show:
	@./scripts/version.sh show

version-set:
	@if [ -z "$(V)" ]; then \
		echo "$(RED)❌ Version is required. Usage: make version-set V=1.0.0$(NC)"; \
		exit 1; \
	fi
	@./scripts/version.sh set $(V)

version-bump-patch:
	@./scripts/version.sh bump patch

version-bump-minor:
	@./scripts/version.sh bump minor

version-bump-major:
	@./scripts/version.sh bump major

# Show help
help:
	@echo "MiauBot Build System"
	@echo ""
	@echo "$(BLUE)Available targets:$(NC)"
	@echo "  $(GREEN)build$(NC)              Build executables for all platforms"
	@echo "  $(GREEN)build-linux-amd64$(NC)  Build for Linux AMD64 specifically"
	@echo "  $(GREEN)clean$(NC)              Clean build artifacts"
	@echo "  $(GREEN)info$(NC)               Show build information"
	@echo "  $(GREEN)test-build$(NC)         Build and test executable"
	@echo "  $(GREEN)quick-test$(NC)         Test Python version without building"
	@echo "  $(GREEN)release$(NC)            Build release version"
	@echo ""
	@echo "$(BLUE)Version Management:$(NC)"
	@echo "  $(GREEN)version-show$(NC)       Show current version information"
	@echo "  $(GREEN)version-set V=x.x.x$(NC) Set specific version"
	@echo "  $(GREEN)version-bump-patch$(NC) Bump patch version (1.0.0 -> 1.0.1)"
	@echo "  $(GREEN)version-bump-minor$(NC) Bump minor version (1.0.0 -> 1.1.0)"
	@echo "  $(GREEN)version-bump-major$(NC) Bump major version (1.0.0 -> 2.0.0)"
	@echo ""
	@echo "$(BLUE)Development:$(NC)"
	@echo "  $(GREEN)dev-setup$(NC)          Set up development environment"
	@echo "  $(GREEN)format$(NC)             Format code with ruff"
	@echo "  $(GREEN)lint$(NC)               Lint code with ruff"
	@echo "  $(GREEN)test$(NC)               Run tests"
	@echo ""
	@echo "$(BLUE)Specific platforms:$(NC)"
	@echo "  $(GREEN)build-linux-arm64$(NC)   Build for Linux ARM64 (cross-compiled)"
	@echo "$(BLUE)Future platforms:$(NC)"
	@echo "  $(YELLOW)build-windows-amd64$(NC) Build for Windows AMD64 (planned)"
	@echo "  $(YELLOW)build-darwin-amd64$(NC)  Build for macOS AMD64 (planned)"
	@echo "  $(YELLOW)build-darwin-arm64$(NC)  Build for macOS ARM64 (planned)"
	@echo ""
	@echo "$(BLUE)Examples:$(NC)"
	@echo "  make build              # Build all platforms"
	@echo "  make clean              # Clean artifacts"
	@echo "  make test-build         # Build and test"
	@echo "  make release            # Full release build"
	@echo "  make version-show       # Show current version"
	@echo "  make version-set V=1.0.0 # Set version to 1.0.0"
	@echo "  make version-bump-patch # Bump patch version" 