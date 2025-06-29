#!/bin/bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VERSION_FILE="$PROJECT_ROOT/VERSION"

# Functions
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

show_current_version() {
    if [ -f "$VERSION_FILE" ]; then
        local version=$(cat "$VERSION_FILE")
        print_status "Current version: $version"
        
        # Show git info if available
        if command -v git >/dev/null 2>&1 && [ -d "$PROJECT_ROOT/.git" ]; then
            local git_hash=$(git -C "$PROJECT_ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown")
            local git_dirty=""
            if ! git -C "$PROJECT_ROOT" diff --quiet 2>/dev/null; then
                git_dirty="-dirty"
            fi
            print_status "Git info: ${git_hash}${git_dirty}"
            print_status "Full version: ${version}+${git_hash}${git_dirty}"
        fi
    else
        print_warning "VERSION file not found"
    fi
}

validate_version() {
    local version="$1"
    if [[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?$ ]]; then
        return 0
    else
        return 1
    fi
}

set_version() {
    local new_version="$1"
    
    if [ -z "$new_version" ]; then
        print_error "Version is required"
        return 1
    fi
    
    if ! validate_version "$new_version"; then
        print_error "Invalid version format: $new_version"
        print_error "Version must follow semantic versioning (e.g., 1.0.0, 1.0.0-beta)"
        return 1
    fi
    
    # Check if version already exists as git tag
    if command -v git >/dev/null 2>&1 && [ -d "$PROJECT_ROOT/.git" ]; then
        if git -C "$PROJECT_ROOT" tag -l | grep -q "^v${new_version}$"; then
            print_error "Version tag v${new_version} already exists"
            return 1
        fi
    fi
    
    print_status "Setting version to: $new_version"
    echo "$new_version" > "$VERSION_FILE"
    print_success "Version updated successfully"
    
    show_current_version
}

bump_version() {
    local bump_type="$1"
    
    if [ ! -f "$VERSION_FILE" ]; then
        print_error "VERSION file not found"
        return 1
    fi
    
    local current_version=$(cat "$VERSION_FILE")
    if ! validate_version "$current_version"; then
        print_error "Current version is invalid: $current_version"
        return 1
    fi
    
    # Parse version components
    local version_regex="^([0-9]+)\.([0-9]+)\.([0-9]+)(-[a-zA-Z0-9]+)?$"
    if [[ $current_version =~ $version_regex ]]; then
        local major="${BASH_REMATCH[1]}"
        local minor="${BASH_REMATCH[2]}"
        local patch="${BASH_REMATCH[3]}"
        local prerelease="${BASH_REMATCH[4]}"
    else
        print_error "Failed to parse current version: $current_version"
        return 1
    fi
    
    local new_version=""
    case "$bump_type" in
        "major")
            new_version="$((major + 1)).0.0"
            ;;
        "minor")
            new_version="${major}.$((minor + 1)).0"
            ;;
        "patch")
            new_version="${major}.${minor}.$((patch + 1))"
            ;;
        *)
            print_error "Invalid bump type: $bump_type"
            print_error "Valid types: major, minor, patch"
            return 1
            ;;
    esac
    
    print_status "Bumping $bump_type version: $current_version -> $new_version"
    set_version "$new_version"
}

show_help() {
    echo "MiauBot Version Management"
    echo
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  show                    Show current version information"
    echo "  set <version>           Set specific version (e.g., 1.0.0)"
    echo "  bump <type>             Bump version by type (major|minor|patch)"
    echo "  help                    Show this help message"
    echo
    echo "Examples:"
    echo "  $0 show                 # Show current version"
    echo "  $0 set 1.0.0            # Set version to 1.0.0"
    echo "  $0 set 1.0.0-beta       # Set pre-release version"
    echo "  $0 bump patch           # Bump patch version (1.0.0 -> 1.0.1)"
    echo "  $0 bump minor           # Bump minor version (1.0.0 -> 1.1.0)"
    echo "  $0 bump major           # Bump major version (1.0.0 -> 2.0.0)"
    echo
}

# Main
main() {
    local command="${1:-show}"
    
    case "$command" in
        "show")
            show_current_version
            ;;
        "set")
            set_version "$2"
            ;;
        "bump")
            bump_version "$2"
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@" 