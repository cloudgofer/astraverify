#!/bin/bash

# Version management script for AstraVerify
# Format: YYYYMM.DD.NN-Beta

VERSION_FILE="VERSION"
DATE=$(date +"%Y.%m.%d")

# Function to get current version
get_current_version() {
    if [ -f "$VERSION_FILE" ]; then
        cat "$VERSION_FILE"
    else
        echo "2025.08.15.00-Beta"
    fi
}

# Function to increment version
increment_version() {
    local current_version=$(get_current_version)
    local current_date=$(echo "$current_version" | cut -d'.' -f1-3)
    local current_counter=$(echo "$current_version" | cut -d'.' -f4 | cut -d'-' -f1)
    
    # If date changed, reset counter to 01
    if [ "$current_date" != "$DATE" ]; then
        echo "${DATE}.01-Beta" > "$VERSION_FILE"
    else
        # Increment counter
        local new_counter=$((10#$current_counter + 1))
        printf "${DATE}.%02d-Beta\n" $new_counter > "$VERSION_FILE"
    fi
    
    echo "Version updated to: $(cat $VERSION_FILE)"
}

# Function to create git tag
create_tag() {
    local version=$(get_current_version)
    local tag_name="v${version}"
    local commit_message="Release version ${version}"
    
    echo "Creating git tag: $tag_name"
    git add "$VERSION_FILE"
    git commit -m "$commit_message"
    git tag "$tag_name"
    
    echo "Tagged version: $tag_name"
}

# Function to show current version
show_version() {
    echo "Current version: $(get_current_version)"
}

# Main script logic
case "$1" in
    "increment")
        increment_version
        ;;
    "tag")
        increment_version
        create_tag
        ;;
    "show")
        show_version
        ;;
    *)
        echo "Usage: $0 {increment|tag|show}"
        echo "  increment - Increment version number"
        echo "  tag      - Increment version and create git tag"
        echo "  show     - Show current version"
        exit 1
        ;;
esac
