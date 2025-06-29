#!/bin/bash

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PLATFORMS=("linux-amd64" "linux-arm64")
BUILD_DIR="./dist"
DOCKERFILE="Dockerfile.build"

# Platform mapping for Docker buildx
declare -A PLATFORM_MAP
PLATFORM_MAP["linux-amd64"]="linux/amd64"
PLATFORM_MAP["linux-arm64"]="linux/arm64"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to build for a specific platform
build_platform() {
    local platform=$1
    local docker_platform="${PLATFORM_MAP[$platform]}"
    
    if [ -z "$docker_platform" ]; then
        print_error "Unknown platform: $platform"
        return 1
    fi
    
    print_status "Building for platform: $platform ($docker_platform)"
    
    # Create temporary directory for this build
    local temp_dir=$(mktemp -d)
    
    # Build the Docker image and extract the executable
    docker buildx build \
        --platform "$docker_platform" \
        --file "$DOCKERFILE" \
        --target export \
        --output "$temp_dir" \
        .
    
    # Find and move the executable
    local executable_file=$(find "$temp_dir" -name "miaubot-linux-*" -type f | head -1)
    
    if [ -n "$executable_file" ] && [ -f "$executable_file" ]; then
        # Move to build directory with correct name
        mv "$executable_file" "$BUILD_DIR/miaubot-$platform"
        
        # Make executable
        chmod +x "$BUILD_DIR/miaubot-$platform"
        
        # Get file size
        local size=$(du -h "$BUILD_DIR/miaubot-$platform" | cut -f1)
        print_success "Built miaubot-$platform (Size: $size)"
        
        # Test the executable (only for native platform)
        if [ "$platform" = "linux-amd64" ]; then
            print_status "Testing executable..."
            if "$BUILD_DIR/miaubot-$platform" --help > /dev/null 2>&1; then
                print_success "Executable test passed"
            else
                print_warning "Executable test failed, but binary was created"
            fi
        else
            print_warning "Skipping test for non-native platform: $platform"
        fi
    else
        print_error "Failed to create executable for $platform"
        rm -rf "$temp_dir"
        return 1
    fi
    
    # Clean up temporary directory
    rm -rf "$temp_dir"
}

# Function to clean build artifacts
clean() {
    print_status "Cleaning build artifacts..."
    rm -rf "$BUILD_DIR"
    docker system prune -f --filter label=stage=builder 2>/dev/null || true
    print_success "Cleaned build artifacts"
}

# Function to show build info
show_info() {
    echo
    echo "🚀 MiauBot Build System"
    echo "======================="
    echo
    echo "Available platforms:"
    for platform in "${PLATFORMS[@]}"; do
        echo "  - $platform"
    done
    echo
    echo "Build directory: $BUILD_DIR"
    echo "Dockerfile: $DOCKERFILE"
    echo
}

# Main build function
build_all() {
    show_info
    
    # Create build directory
    mkdir -p "$BUILD_DIR"
    
    print_status "Starting build process..."
    local start_time=$(date +%s)
    
    # Build for each platform
    for platform in "${PLATFORMS[@]}"; do
        build_platform "$platform"
        echo
    done
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_success "Build completed in ${duration}s"
    
    # Show results
    echo
    echo "📦 Build Results:"
    echo "=================="
    if [ -d "$BUILD_DIR" ]; then
        ls -lah "$BUILD_DIR/"
    fi
    
    echo
    echo "🎯 Usage:"
    echo "========="
    echo "./dist/miaubot-linux-amd64 --help"
    echo "./dist/miaubot-linux-amd64 --input /path/to/anime --report-only --remote-base 'gdrive:Anime'"
}

# Check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not available"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
}

# Help function
show_help() {
    echo "MiauBot Build System"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  build    Build executables for all platforms (default)"
    echo "  clean    Clean build artifacts and Docker cache"
    echo "  info     Show build information"
    echo "  help     Show this help message"
    echo
    echo "Examples:"
    echo "  $0                 # Build all platforms"
    echo "  $0 build           # Build all platforms"
    echo "  $0 clean           # Clean build artifacts"
    echo
}

# Main script
main() {
    local command=${1:-build}
    
    case $command in
        build)
            check_docker
            build_all
            ;;
        clean)
            clean
            ;;
        info)
            show_info
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 