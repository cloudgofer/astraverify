#!/bin/bash

# AstraVerify Deployment Prerequisites Validation Script
# Validates all requirements before deployment

set -e

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

# Function to validate git installation
validate_git() {
    print_status "Validating Git installation..."
    if command -v git &> /dev/null; then
        print_success "Git is installed: $(git --version)"
    else
        print_error "Git is not installed. Please install Git first."
        exit 1
    fi
}

# Function to validate git repository
validate_git_repo() {
    print_status "Validating Git repository..."
    if [ -d ".git" ]; then
        print_success "Git repository found"
    else
        print_error "Not in a Git repository. Please run this script from the project root."
        exit 1
    fi
}

# Function to validate remote repository
validate_remote() {
    print_status "Validating remote repository..."
    if git remote get-url origin &> /dev/null; then
        print_success "Remote origin configured: $(git remote get-url origin)"
    else
        print_error "No remote origin configured. Please add remote repository."
        exit 1
    fi
}

# Function to validate working directory
validate_working_directory() {
    print_status "Validating working directory..."
    if [ -n "$(git status --porcelain)" ]; then
        print_error "Working directory is not clean. Please commit or stash changes."
        git status --short
        exit 1
    else
        print_success "Working directory is clean"
    fi
}

# Function to validate current branch
validate_current_branch() {
    local required_branch="$1"
    local current_branch=$(git branch --show-current)
    
    print_status "Validating current branch..."
    print_status "Current branch: $current_branch"
    print_status "Required branch: $required_branch"
    
    if [ "$current_branch" = "$required_branch" ]; then
        print_success "✅ On correct branch: $required_branch"
    else
        print_error "❌ Wrong branch. Current: $current_branch, Required: $required_branch"
        print_status "To fix: git checkout $required_branch"
        exit 1
    fi
}

# Function to validate branch synchronization
validate_branch_sync() {
    local source_branch="$1"
    local target_branch="$2"
    
    print_status "Validating $source_branch → $target_branch synchronization..."
    
    # Fetch latest changes
    git fetch origin
    
    # Check if source branch exists
    if ! git show-ref --verify --quiet refs/remotes/origin/$source_branch; then
        print_error "❌ Source branch $source_branch does not exist on remote"
        exit 1
    fi
    
    # Check if target branch exists
    if ! git show-ref --verify --quiet refs/remotes/origin/$target_branch; then
        print_warning "⚠️  Target branch $target_branch does not exist on remote"
        print_status "This will be created during deployment"
        return 0
    fi
    
    # Check if source is merged into target
    if git merge-base --is-ancestor "origin/$source_branch" "origin/$target_branch" 2>/dev/null; then
        print_success "✅ $source_branch is merged into $target_branch"
    else
        print_error "❌ $source_branch is NOT merged into $target_branch"
        print_status "To fix: git checkout $target_branch && git merge origin/$source_branch"
        exit 1
    fi
}

# Function to validate deployment scripts
validate_deployment_scripts() {
    print_status "Validating deployment scripts..."
    
    local scripts=(
        "deploy/deploy_local.sh"
        "deploy/deploy_staging.sh"
        "deploy/deploy_production.sh"
        "version.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ] && [ -x "$script" ]; then
            print_success "✅ $script exists and is executable"
        elif [ -f "$script" ]; then
            print_warning "⚠️  $script exists but is not executable"
            print_status "To fix: chmod +x $script"
        else
            print_error "❌ $script does not exist"
            exit 1
        fi
    done
}

# Function to validate version file
validate_version_file() {
    print_status "Validating version file..."
    
    if [ -f "VERSION" ]; then
        local version=$(cat VERSION)
        print_success "✅ Version file exists: $version"
    else
        print_error "❌ VERSION file does not exist"
        exit 1
    fi
}

# Function to validate gcloud CLI
validate_gcloud() {
    print_status "Validating Google Cloud CLI..."
    
    if command -v gcloud &> /dev/null; then
        print_success "✅ gcloud CLI is installed: $(gcloud --version | head -1)"
        
        # Check authentication
        if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
            print_success "✅ gcloud is authenticated"
        else
            print_error "❌ gcloud is not authenticated. Please run: gcloud auth login"
            exit 1
        fi
        
        # Check project
        local project=$(gcloud config get-value project 2>/dev/null)
        if [ -n "$project" ]; then
            print_success "✅ gcloud project set: $project"
        else
            print_error "❌ gcloud project not set. Please run: gcloud config set project astraverify"
            exit 1
        fi
    else
        print_error "❌ gcloud CLI is not installed. Please install Google Cloud SDK."
        exit 1
    fi
}

# Function to validate Node.js and npm
validate_node() {
    print_status "Validating Node.js and npm..."
    
    if command -v node &> /dev/null; then
        print_success "✅ Node.js is installed: $(node --version)"
    else
        print_error "❌ Node.js is not installed. Please install Node.js."
        exit 1
    fi
    
    if command -v npm &> /dev/null; then
        print_success "✅ npm is installed: $(npm --version)"
    else
        print_error "❌ npm is not installed. Please install npm."
        exit 1
    fi
}

# Function to validate environment-specific requirements
validate_environment() {
    local environment="$1"
    
    print_status "Validating $environment environment requirements..."
    
    case "$environment" in
        "local")
            validate_current_branch "develop"
            ;;
        "stage")
            validate_current_branch "develop"
            validate_branch_sync "develop" "$MONTHLY_BRANCH"
            ;;
        "prod")
            validate_current_branch "main"
            validate_branch_sync "$MONTHLY_BRANCH" "main"
            validate_gcloud
            ;;
        *)
            print_error "Unknown environment: $environment"
            exit 1
            ;;
    esac
}

# Main validation function
main() {
    local environment="$1"
    
    echo "AstraVerify Deployment Prerequisites Validation"
    echo "==============================================="
    echo ""
    
    # Basic validations
    validate_git
    validate_git_repo
    validate_remote
    validate_working_directory
    validate_deployment_scripts
    validate_version_file
    validate_node
    
    # Environment-specific validations
    if [ -n "$environment" ]; then
        validate_environment "$environment"
    fi
    
    echo ""
    print_success "✅ All prerequisites validated successfully!"
    
    if [ -n "$environment" ]; then
        print_status "Ready to deploy to $environment environment"
    else
        print_status "Ready for deployment (specify environment for specific validation)"
    fi
}

# Script usage
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "AstraVerify Deployment Prerequisites Validation"
    echo ""
    echo "Usage: $0 [environment]"
    echo ""
    echo "Environments:"
    echo "  local  - Validate LOCAL deployment prerequisites"
    echo "  stage  - Validate STAGE deployment prerequisites"
    echo "  prod   - Validate PROD deployment prerequisites"
    echo ""
    echo "Examples:"
    echo "  $0         - Validate basic prerequisites"
    echo "  $0 local   - Validate LOCAL deployment prerequisites"
    echo "  $0 stage   - Validate STAGE deployment prerequisites"
    echo "  $0 prod    - Validate PROD deployment prerequisites"
    exit 0
fi

# Run validation
main "$1"
