#!/bin/bash

# AstraVerify DevOps Branching Strategy Enforcement Script
# Enforces: LOCAL -> develop, STAGE -> monthly branch, PROD -> main with tagging

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Configuration
CURRENT_YEAR=$(date +%Y)
CURRENT_MONTH=$(date +%m)
MONTHLY_BRANCH="release/${CURRENT_YEAR}-${CURRENT_MONTH}"
VERSION_FILE="VERSION"

# Function to validate git status
validate_git_status() {
    if [ -n "$(git status --porcelain)" ]; then
        print_error "Working directory is not clean. Please commit or stash changes."
        git status --short
        exit 1
    fi
    
    if ! git fetch origin; then
        print_error "Failed to fetch from remote repository."
        exit 1
    fi
}

# Function to get current version
get_current_version() {
    if [ -f "$VERSION_FILE" ]; then
        cat "$VERSION_FILE"
    else
        echo "2025.08.15.00-Beta"
    fi
}

# Function to increment version for production
increment_production_version() {
    local current_version=$(get_current_version)
    local current_date=$(echo "$current_version" | cut -d'.' -f1-3)
    local current_counter=$(echo "$current_version" | cut -d'.' -f4 | cut -d'-' -f1)
    
    # If date changed, reset counter to 01
    local today=$(date +"%Y.%m.%d")
    if [ "$current_date" != "$today" ]; then
        echo "${today}.01-Beta" > "$VERSION_FILE"
    else
        # Increment counter
        local new_counter=$((10#$current_counter + 1))
        printf "${today}.%02d-Beta\n" $new_counter > "$VERSION_FILE"
    fi
    
    echo "Version updated to: $(cat $VERSION_FILE)"
}

# Function to create production tag
create_production_tag() {
    local version=$(get_current_version)
    local tag_name="v${version}"
    
    print_status "Creating production tag: $tag_name"
    
    git add "$VERSION_FILE"
    git commit -m "Release version ${version} for production deployment"
    git tag "$tag_name"
    git push origin "$tag_name"
    
    print_success "Production tag created: $tag_name"
    echo "$tag_name"
}

# Function to validate develop is merged into monthly branch
validate_stage_deployment() {
    local monthly_branch="$1"
    
    print_status "Validating that develop is merged into $monthly_branch..."
    
    # Check if monthly branch exists
    if ! git show-ref --verify --quiet refs/remotes/origin/$monthly_branch; then
        print_error "Monthly branch $monthly_branch does not exist on remote."
        print_status "Creating monthly branch from develop..."
        git checkout develop
        git pull origin develop
        git checkout -b "$monthly_branch"
        git push -u origin "$monthly_branch"
        print_success "Created monthly branch: $monthly_branch"
        return 0
    fi
    
    # Get the latest commit hash of develop
    local develop_commit=$(git rev-parse origin/develop)
    
    # Check if develop commit is in monthly branch
    if git merge-base --is-ancestor "$develop_commit" "origin/$monthly_branch"; then
        print_success "✅ develop is merged into $monthly_branch"
        return 0
    else
        print_error "❌ develop is NOT merged into $monthly_branch"
        print_status "Merging develop into $monthly_branch..."
        
        git checkout "$monthly_branch"
        git pull origin "$monthly_branch"
        git merge origin/develop --no-edit
        git push origin "$monthly_branch"
        
        print_success "✅ Successfully merged develop into $monthly_branch"
        return 0
    fi
}

# Function to deploy to LOCAL environment
deploy_local() {
    print_status "Starting LOCAL deployment from develop branch..."
    
    # Ensure we're on develop branch
    if [ "$(git branch --show-current)" != "develop" ]; then
        print_error "LOCAL deployment must be done from develop branch"
        print_status "Switching to develop branch..."
        git checkout develop
        git pull origin develop
    fi
    
    validate_git_status
    
    print_status "Deploying to LOCAL environment..."
    ./deploy/deploy_local.sh
    
    print_success "LOCAL deployment completed successfully!"
}

# Function to deploy to STAGE environment
deploy_stage() {
    print_status "Starting STAGE deployment from monthly branch: $MONTHLY_BRANCH"
    
    validate_git_status
    
    # Validate develop is merged into monthly branch
    validate_stage_deployment "$MONTHLY_BRANCH"
    
    # Switch to monthly branch
    git checkout "$MONTHLY_BRANCH"
    git pull origin "$MONTHLY_BRANCH"
    
    print_status "Deploying to STAGE environment..."
    ./deploy/deploy_staging.sh
    
    print_success "STAGE deployment completed successfully!"
}

# Function to deploy to PROD environment
deploy_prod() {
    print_status "Starting PROD deployment from main branch..."
    
    # Ensure we're on main branch
    if [ "$(git branch --show-current)" != "main" ]; then
        print_error "PROD deployment must be done from main branch"
        print_status "Switching to main branch..."
        git checkout main
        git pull origin main
    fi
    
    validate_git_status
    
    # Confirm production deployment
    echo ""
    print_warning "⚠️  WARNING: This will deploy to PRODUCTION environment!"
    print_warning "This will affect live users. Are you sure you want to continue?"
    echo ""
    read -p "Type 'yes' to confirm production deployment: " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_error "Production deployment cancelled."
        exit 1
    fi
    
    # Create production tag
    local tag_name=$(create_production_tag)
    
    print_status "Deploying to PROD environment with tag: $tag_name"
    ./deploy/deploy_production.sh
    
    print_success "PROD deployment completed successfully with tag: $tag_name"
}

# Function to rollback to last tag
rollback_to_last_tag() {
    print_warning "Starting rollback to last production tag..."
    
    # Get the last production tag
    local last_tag=$(git tag --sort=-version:refname | grep "^v[0-9]" | head -1)
    
    if [ -z "$last_tag" ]; then
        print_error "No production tags found for rollback."
        exit 1
    fi
    
    print_status "Rolling back to tag: $last_tag"
    
    # Create rollback branch
    local rollback_branch="hotfix/rollback-$(date +%Y%m%d-%H%M%S)"
    git checkout -b "$rollback_branch" "$last_tag"
    git push origin "$rollback_branch"
    
    print_success "Rollback branch created: $rollback_branch"
    print_status "To complete rollback:"
    print_status "1. Merge $rollback_branch into main"
    print_status "2. Deploy from main branch"
    print_status "3. Delete rollback branch when confirmed"
}

# Function to show deployment status
show_status() {
    print_status "Current Git Branching Strategy Status:"
    echo ""
    
    local current_branch=$(git branch --show-current)
    print_status "Current branch: $current_branch"
    
    local develop_commit=$(git rev-parse origin/develop --short 2>/dev/null || echo "N/A")
    local main_commit=$(git rev-parse origin/main --short 2>/dev/null || echo "N/A")
    local monthly_commit=$(git rev-parse "origin/$MONTHLY_BRANCH" --short 2>/dev/null || echo "N/A")
    
    print_status "Latest commits:"
    echo "  develop: $develop_commit"
    echo "  main: $main_commit"
    echo "  $MONTHLY_BRANCH: $monthly_commit"
    
    local current_version=$(get_current_version)
    print_status "Current version: $current_version"
    
    local last_tag=$(git tag --sort=-version:refname | grep "^v[0-9]" | head -1)
    print_status "Last production tag: $last_tag"
    
    echo ""
    print_status "Branch synchronization status:"
    
    # Check if develop is merged into monthly branch
    if git merge-base --is-ancestor "origin/develop" "origin/$MONTHLY_BRANCH" 2>/dev/null; then
        echo "  ✅ develop → $MONTHLY_BRANCH: SYNCED"
    else
        echo "  ❌ develop → $MONTHLY_BRANCH: NOT SYNCED"
    fi
    
    # Check if monthly branch is merged into main
    if git merge-base --is-ancestor "origin/$MONTHLY_BRANCH" "origin/main" 2>/dev/null; then
        echo "  ✅ $MONTHLY_BRANCH → main: SYNCED"
    else
        echo "  ❌ $MONTHLY_BRANCH → main: NOT SYNCED"
    fi
}

# Main script logic
case "$1" in
    "local")
        deploy_local
        ;;
    "stage")
        deploy_stage
        ;;
    "prod")
        deploy_prod
        ;;
    "rollback")
        rollback_to_last_tag
        ;;
    "status")
        show_status
        ;;
    "validate-stage")
        validate_stage_deployment "$MONTHLY_BRANCH"
        ;;
    "create-tag")
        create_production_tag
        ;;
    *)
        echo "AstraVerify DevOps Branching Strategy Enforcement"
        echo ""
        echo "Usage: $0 {local|stage|prod|rollback|status|validate-stage|create-tag}"
        echo ""
        echo "Commands:"
        echo "  local         - Deploy to LOCAL environment from develop branch"
        echo "  stage         - Deploy to STAGE environment from monthly branch"
        echo "  prod          - Deploy to PROD environment from main branch with tagging"
        echo "  rollback      - Create rollback branch from last production tag"
        echo "  status        - Show current branching strategy status"
        echo "  validate-stage - Validate develop is merged into monthly branch"
        echo "  create-tag    - Create production tag without deploying"
        echo ""
        echo "Branching Strategy:"
        echo "  LOCAL:  develop branch"
        echo "  STAGE:  $MONTHLY_BRANCH (monthly branch)"
        echo "  PROD:   main branch with version tagging"
        echo ""
        echo "Tag Format: vYYYY.MM.DD.NN (e.g., v2025.08.15.01)"
        exit 1
        ;;
esac
