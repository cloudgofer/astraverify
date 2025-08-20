#!/bin/bash

# Comprehensive STAGE Environment Test Runner
# Tests security features, rate limiting, abuse prevention, and mobile responsiveness

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
STAGING_API_URL="https://astraverify-backend-staging-ml2mhibdvq-uc.a.run.app"
STAGING_FRONTEND_URL="https://astraverify-frontend-staging-ml2mhibdvq-uc.a.run.app"

# Test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Utility functions
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

error() {
    echo -e "${RED}❌ $1${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed"
        exit 1
    fi
    success "Node.js is installed"
    
    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        error "npm is not installed"
        exit 1
    fi
    success "npm is installed"
    
    # Check if curl is installed
    if ! command -v curl &> /dev/null; then
        error "curl is not installed"
        exit 1
    fi
    success "curl is installed"
    
    # Install required npm packages
    log "Installing required npm packages..."
    npm install --silent
    success "npm packages installed"
}

# Test 1: Basic connectivity
test_connectivity() {
    log "Testing basic connectivity..."
    
    # Test API health endpoint
    if curl -s -f "${STAGING_API_URL}/api/health" > /dev/null; then
        success "API health endpoint is accessible"
    else
        error "API health endpoint is not accessible"
    fi
    
    # Test frontend accessibility
    if curl -s -f "${STAGING_FRONTEND_URL}" > /dev/null; then
        success "Frontend is accessible"
    else
        error "Frontend is not accessible"
    fi
}

# Test 2: Security features
test_security_features() {
    log "Testing security features..."
    
    # Run security test suite
    if node test_security_features.js; then
        success "Security features test suite completed"
    else
        error "Security features test suite failed"
    fi
}

# Test 3: Rate limiting and abuse prevention
test_rate_limiting() {
    log "Testing rate limiting and abuse prevention..."
    
    # Run comprehensive test suite
    if node test_stage_environment.js; then
        success "Rate limiting and abuse prevention test suite completed"
    else
        error "Rate limiting and abuse prevention test suite failed"
    fi
}

# Test 4: Mobile responsiveness
test_mobile_responsiveness() {
    log "Testing mobile responsiveness..."
    
    # Check if Puppeteer is available
    if ! node -e "require('puppeteer')" 2>/dev/null; then
        warning "Puppeteer not found, installing..."
        npm install puppeteer --silent
    fi
    
    # Run mobile responsiveness test suite
    if node test_mobile_responsiveness.js; then
        success "Mobile responsiveness test suite completed"
    else
        error "Mobile responsiveness test suite failed"
    fi
}

# Test 5: API functionality
test_api_functionality() {
    log "Testing API functionality..."
    
    # Test domain check with valid domain
    response=$(curl -s -X POST "${STAGING_API_URL}/api/check" \
        -H "Content-Type: application/json" \
        -d '{"domain": "gmail.com"}' \
        -w "%{http_code}")
    
    http_code="${response: -3}"
    if [ "$http_code" = "200" ]; then
        success "API domain check with valid domain"
    else
        error "API domain check failed with HTTP code: $http_code"
    fi
    
    # Test domain check with invalid domain
    response=$(curl -s -X POST "${STAGING_API_URL}/api/check" \
        -H "Content-Type: application/json" \
        -d '{"domain": "invalid-domain-12345.com"}' \
        -w "%{http_code}")
    
    http_code="${response: -3}"
    if [ "$http_code" = "400" ] || [ "$http_code" = "422" ]; then
        success "API domain check correctly rejected invalid domain"
    else
        error "API domain check should have rejected invalid domain, got HTTP code: $http_code"
    fi
}

# Test 6: Email functionality
test_email_functionality() {
    log "Testing email functionality..."
    
    # Test email report endpoint
    response=$(curl -s -X POST "${STAGING_API_URL}/api/email-report" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "test@example.com",
            "domain": "gmail.com",
            "analysis_result": {"security_score": 85},
            "opt_in_marketing": false
        }' \
        -w "%{http_code}")
    
    http_code="${response: -3}"
    if [ "$http_code" = "200" ]; then
        success "Email report functionality working"
    else
        warning "Email report functionality returned HTTP code: $http_code"
    fi
}

# Test 7: Performance and load testing
test_performance() {
    log "Testing performance and load..."
    
    # Test response time for health endpoint
    start_time=$(date +%s%N)
    curl -s -f "${STAGING_API_URL}/api/health" > /dev/null
    end_time=$(date +%s%N)
    
    response_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
    
    if [ $response_time -lt 1000 ]; then
        success "Health endpoint response time: ${response_time}ms (acceptable)"
    else
        warning "Health endpoint response time: ${response_time}ms (slow)"
    fi
    
    # Test concurrent requests
    log "Testing concurrent requests..."
    for i in {1..5}; do
        curl -s -X POST "${STAGING_API_URL}/api/check" \
            -H "Content-Type: application/json" \
            -d '{"domain": "gmail.com"}' > /dev/null &
    done
    wait
    
    success "Concurrent requests test completed"
}

# Test 8: Error handling
test_error_handling() {
    log "Testing error handling..."
    
    # Test with malformed JSON
    response=$(curl -s -X POST "${STAGING_API_URL}/api/check" \
        -H "Content-Type: application/json" \
        -d '{"domain": "gmail.com"' \
        -w "%{http_code}")
    
    http_code="${response: -3}"
    if [ "$http_code" = "400" ]; then
        success "API correctly handles malformed JSON"
    else
        error "API should handle malformed JSON, got HTTP code: $http_code"
    fi
    
    # Test with wrong content type
    response=$(curl -s -X POST "${STAGING_API_URL}/api/check" \
        -H "Content-Type: text/plain" \
        -d '{"domain": "gmail.com"}' \
        -w "%{http_code}")
    
    http_code="${response: -3}"
    if [ "$http_code" = "400" ] || [ "$http_code" = "415" ]; then
        success "API correctly handles wrong content type"
    else
        warning "API content type handling returned HTTP code: $http_code"
    fi
}

# Generate final report
generate_report() {
    log "Generating final test report..."
    
    success_rate=$(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0")
    
    echo ""
    echo "=========================================="
    echo "           STAGE ENVIRONMENT TEST REPORT"
    echo "=========================================="
    echo "Timestamp: $(date)"
    echo "Environment: STAGING"
    echo "API URL: $STAGING_API_URL"
    echo "Frontend URL: $STAGING_FRONTEND_URL"
    echo ""
    echo "Test Results:"
    echo "  Total Tests: $TOTAL_TESTS"
    echo "  Passed: $PASSED_TESTS"
    echo "  Failed: $FAILED_TESTS"
    echo "  Success Rate: ${success_rate}%"
    echo ""
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed! STAGE environment is ready.${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠️ $FAILED_TESTS tests failed. Please review the results.${NC}"
        exit 1
    fi
}

# Main test execution
main() {
    echo -e "${BLUE}🚀 Starting Comprehensive STAGE Environment Tests${NC}"
    echo "=========================================="
    echo "API URL: $STAGING_API_URL"
    echo "Frontend URL: $STAGING_FRONTEND_URL"
    echo "=========================================="
    echo ""
    
    # Run all test suites
    check_prerequisites
    test_connectivity
    test_security_features
    test_rate_limiting
    test_mobile_responsiveness
    test_api_functionality
    test_email_functionality
    test_performance
    test_error_handling
    
    # Generate final report
    generate_report
}

# Handle script interruption
trap 'echo -e "\n${RED}Test interrupted by user${NC}"; exit 1' INT

# Run main function
main "$@"
