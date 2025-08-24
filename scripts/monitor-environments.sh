#!/bin/bash

# AstraVerify Environment Monitoring Script
# Continuously monitors all environments for health and configuration issues

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[MONITOR]${NC} $1"
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
LOCAL_BACKEND_URL="http://localhost:8080"
LOCAL_FRONTEND_URL="http://localhost:3000"
STAGING_BACKEND_URL="https://astraverify-backend-staging-ml2mhibdvq-uc.a.run.app"
STAGING_FRONTEND_URL="https://astraverify-frontend-staging-ml2mhibdvq-uc.a.run.app"
PRODUCTION_BACKEND_URL="https://astraverify-backend-ml2mhibdvq-uc.a.run.app"
PRODUCTION_FRONTEND_URL="https://astraverify-frontend-ml2mhibdvq-uc.a.run.app"

# Function to check service health
check_service_health() {
    local service_name=$1
    local url=$2
    local timeout=${3:-10}
    
    if curl -f -s --max-time $timeout "$url" > /dev/null 2>&1; then
        print_success "$service_name is healthy: $url"
        return 0
    else
        print_error "$service_name is unhealthy: $url"
        return 1
    fi
}

# Function to check API functionality
check_api_functionality() {
    local environment=$1
    local backend_url=$2
    
    print_status "Testing API functionality for $environment..."
    
    # Test basic API endpoint
    local response=$(curl -s --max-time 10 "$backend_url/api/check?domain=example.com" 2>/dev/null || echo "")
    
    if [ -n "$response" ] && echo "$response" | grep -q "example.com"; then
        print_success "$environment API is working correctly"
        return 0
    else
        print_error "$environment API is not working correctly"
        return 1
    fi
}

# Function to check domain analysis
check_domain_analysis() {
    local environment=$1
    local backend_url=$2
    
    print_status "Testing domain analysis for $environment..."
    
    # Test domain analysis with progressive loading
    local response=$(curl -s --max-time 30 "$backend_url/api/check?domain=google.com&progressive=true" 2>/dev/null || echo "")
    
    if [ -n "$response" ] && echo "$response" | grep -q "google.com"; then
        print_success "$environment domain analysis is working"
        return 0
    else
        print_error "$environment domain analysis is not working"
        return 1
    fi
}

# Function to check configuration consistency
check_configuration_consistency() {
    local environment=$1
    local frontend_url=$2
    local expected_backend_url=$3
    
    print_status "Checking configuration consistency for $environment..."
    
    # Get frontend HTML and check for backend URL
    local frontend_html=$(curl -s --max-time 10 "$frontend_url" 2>/dev/null || echo "")
    
    if [ -n "$frontend_html" ]; then
        if echo "$frontend_html" | grep -q "$expected_backend_url"; then
            print_success "$environment frontend is configured correctly"
            return 0
        else
            print_error "$environment frontend configuration mismatch"
            print_status "Expected: $expected_backend_url"
            return 1
        fi
    else
        print_error "Could not fetch $environment frontend"
        return 1
    fi
}

# Function to check local environment
check_local_environment() {
    print_status "Checking LOCAL environment..."
    
    local local_healthy=true
    
    # Check if services are running
    if ! check_service_health "Local Backend" "$LOCAL_BACKEND_URL" 5; then
        local_healthy=false
    fi
    
    if ! check_service_health "Local Frontend" "$LOCAL_FRONTEND_URL" 5; then
        local_healthy=false
    fi
    
    # Check API functionality if backend is running
    if [ "$local_healthy" = true ]; then
        if ! check_api_functionality "Local" "$LOCAL_BACKEND_URL"; then
            local_healthy=false
        fi
        
        if ! check_domain_analysis "Local" "$LOCAL_BACKEND_URL"; then
            local_healthy=false
        fi
        
        if ! check_configuration_consistency "Local" "$LOCAL_FRONTEND_URL" "localhost:8080"; then
            local_healthy=false
        fi
    fi
    
    if [ "$local_healthy" = true ]; then
        print_success "LOCAL environment is healthy"
        return 0
    else
        print_error "LOCAL environment has issues"
        return 1
    fi
}

# Function to check staging environment
check_staging_environment() {
    print_status "Checking STAGING environment..."
    
    local staging_healthy=true
    
    # Check if services are running
    if ! check_service_health "Staging Backend" "$STAGING_BACKEND_URL"; then
        staging_healthy=false
    fi
    
    if ! check_service_health "Staging Frontend" "$STAGING_FRONTEND_URL"; then
        staging_healthy=false
    fi
    
    # Check API functionality if backend is running
    if [ "$staging_healthy" = true ]; then
        if ! check_api_functionality "Staging" "$STAGING_BACKEND_URL"; then
            staging_healthy=false
        fi
        
        if ! check_domain_analysis "Staging" "$STAGING_BACKEND_URL"; then
            staging_healthy=false
        fi
        
        if ! check_configuration_consistency "Staging" "$STAGING_FRONTEND_URL" "astraverify-backend-staging"; then
            staging_healthy=false
        fi
    fi
    
    if [ "$staging_healthy" = true ]; then
        print_success "STAGING environment is healthy"
        return 0
    else
        print_error "STAGING environment has issues"
        return 1
    fi
}

# Function to check production environment
check_production_environment() {
    print_status "Checking PRODUCTION environment..."
    
    local production_healthy=true
    
    # Check if services are running
    if ! check_service_health "Production Backend" "$PRODUCTION_BACKEND_URL"; then
        production_healthy=false
    fi
    
    if ! check_service_health "Production Frontend" "$PRODUCTION_FRONTEND_URL"; then
        production_healthy=false
    fi
    
    # Check API functionality if backend is running
    if [ "$production_healthy" = true ]; then
        if ! check_api_functionality "Production" "$PRODUCTION_BACKEND_URL"; then
            production_healthy=false
        fi
        
        if ! check_domain_analysis "Production" "$PRODUCTION_BACKEND_URL"; then
            production_healthy=false
        fi
        
        if ! check_configuration_consistency "Production" "$PRODUCTION_FRONTEND_URL" "astraverify-backend-ml2mhibdvq-uc.a.run.app"; then
            production_healthy=false
        fi
    fi
    
    if [ "$production_healthy" = true ]; then
        print_success "PRODUCTION environment is healthy"
        return 0
    else
        print_error "PRODUCTION environment has issues"
        return 1
    fi
}

# Function to generate health report
generate_health_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local report_file="health_report_$(date '+%Y%m%d_%H%M%S').txt"
    
    print_status "Generating health report: $report_file"
    
    {
        echo "AstraVerify Health Report"
        echo "Generated: $timestamp"
        echo "=================================="
        echo ""
        
        echo "LOCAL Environment:"
        if check_local_environment > /dev/null 2>&1; then
            echo "✅ HEALTHY"
        else
            echo "❌ UNHEALTHY"
        fi
        echo ""
        
        echo "STAGING Environment:"
        if check_staging_environment > /dev/null 2>&1; then
            echo "✅ HEALTHY"
        else
            echo "❌ UNHEALTHY"
        fi
        echo ""
        
        echo "PRODUCTION Environment:"
        if check_production_environment > /dev/null 2>&1; then
            echo "✅ HEALTHY"
        else
            echo "❌ UNHEALTHY"
        fi
        echo ""
        
        echo "Configuration URLs:"
        echo "Local Backend: $LOCAL_BACKEND_URL"
        echo "Local Frontend: $LOCAL_FRONTEND_URL"
        echo "Staging Backend: $STAGING_BACKEND_URL"
        echo "Staging Frontend: $STAGING_FRONTEND_URL"
        echo "Production Backend: $PRODUCTION_BACKEND_URL"
        echo "Production Frontend: $PRODUCTION_FRONTEND_URL"
        
    } > "$report_file"
    
    print_success "Health report saved to: $report_file"
}

# Function to run continuous monitoring
run_continuous_monitoring() {
    local interval=${1:-300}  # Default 5 minutes
    local max_failures=${2:-3}  # Default 3 consecutive failures
    
    print_status "Starting continuous monitoring (interval: ${interval}s, max failures: $max_failures)"
    
    local local_failures=0
    local staging_failures=0
    local production_failures=0
    
    while true; do
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        print_status "Health check at $timestamp"
        
        # Check local environment
        if check_local_environment; then
            local_failures=0
        else
            ((local_failures++))
            if [ $local_failures -ge $max_failures ]; then
                print_error "LOCAL environment has been unhealthy for $local_failures consecutive checks"
            fi
        fi
        
        # Check staging environment
        if check_staging_environment; then
            staging_failures=0
        else
            ((staging_failures++))
            if [ $staging_failures -ge $max_failures ]; then
                print_error "STAGING environment has been unhealthy for $staging_failures consecutive checks"
            fi
        fi
        
        # Check production environment
        if check_production_environment; then
            production_failures=0
        else
            ((production_failures++))
            if [ $production_failures -ge $max_failures ]; then
                print_error "PRODUCTION environment has been unhealthy for $production_failures consecutive checks"
            fi
        fi
        
        print_status "Waiting $interval seconds until next check..."
        sleep $interval
    done
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [options] [environment]"
    echo ""
    echo "Environments:"
    echo "  local       - Check local environment only"
    echo "  staging     - Check staging environment only"
    echo "  production  - Check production environment only"
    echo "  all         - Check all environments (default)"
    echo ""
    echo "Options:"
    echo "  --continuous [interval]  - Run continuous monitoring (default: 300s)"
    echo "  --report                 - Generate health report"
    echo "  --help                   - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                        # Check all environments once"
    echo "  $0 local                  # Check local environment only"
    echo "  $0 --continuous 60        # Run continuous monitoring every 60 seconds"
    echo "  $0 --report               # Generate health report"
}

# Main function
main() {
    local environment="all"
    local continuous=false
    local interval=300
    local generate_report=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --continuous)
                continuous=true
                if [[ $2 =~ ^[0-9]+$ ]]; then
                    interval=$2
                    shift
                fi
                shift
                ;;
            --report)
                generate_report=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            local|staging|production|all)
                environment=$1
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Generate report if requested
    if [ "$generate_report" = true ]; then
        generate_health_report
        exit 0
    fi
    
    # Run continuous monitoring if requested
    if [ "$continuous" = true ]; then
        run_continuous_monitoring $interval
        exit 0
    fi
    
    # Run single health check
    print_status "Starting health check for $environment environment(s)..."
    
    case $environment in
        "local")
            check_local_environment
            ;;
        "staging")
            check_staging_environment
            ;;
        "production")
            check_production_environment
            ;;
        "all")
            local all_healthy=true
            
            if ! check_local_environment; then
                all_healthy=false
            fi
            
            if ! check_staging_environment; then
                all_healthy=false
            fi
            
            if ! check_production_environment; then
                all_healthy=false
            fi
            
            if [ "$all_healthy" = true ]; then
                print_success "All environments are healthy"
                exit 0
            else
                print_error "Some environments have issues"
                exit 1
            fi
            ;;
        *)
            print_error "Unknown environment: $environment"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
