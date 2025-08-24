#!/bin/bash

# AstraVerify Cloud Run Production Environment Monitor
# Continuously monitors Cloud Run production environment and prevents downtime

set -euo pipefail

# Configuration
PROJECT_ID="astraverify"
SERVICE_NAME="astraverify-backend"
REGION="us-central1"
MONITOR_INTERVAL=60  # seconds
ALERT_THRESHOLD=3    # consecutive failures before alert
LOG_FILE="cloudrun_monitor_$(date +%Y%m%d_%H%M%S).log"
ALERT_LOG="cloudrun_alerts.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Monitoring state
failure_count=0
last_alert_time=0
alert_cooldown=300  # 5 minutes between alerts

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

alert() {
    local message="$1"
    local current_time=$(date +%s)
    
    # Check if enough time has passed since last alert
    if ((current_time - last_alert_time >= alert_cooldown)); then
        echo -e "${RED}[ALERT]${NC} $message" | tee -a "$ALERT_LOG"
        last_alert_time=$current_time
        
        # Send alert (you can customize this)
        send_alert "$message"
    fi
}

send_alert() {
    local message="$1"
    # Add your alert mechanism here (email, Slack, etc.)
    # For now, just log to a separate file
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] CLOUDRUN ALERT: $message" >> "$ALERT_LOG"
}

get_service_url() {
    local service_url
    if [[ -f .service_url ]]; then
        service_url=$(cat .service_url)
    else
        service_url=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)" 2>/dev/null)
        if [[ -n "$service_url" ]]; then
            echo "$service_url" > .service_url
        fi
    fi
    echo "$service_url"
}

check_cloud_run_status() {
    log "Checking Cloud Run service status..."
    
    # Check if service exists and is running
    if ! gcloud run services describe "$SERVICE_NAME" --region="$REGION" >/dev/null 2>&1; then
        alert "Cloud Run service not found or not accessible"
        return 1
    fi
    
    # Check service status
    local service_status=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.conditions[0].status)" 2>/dev/null)
    if [[ "$service_status" != "True" ]]; then
        alert "Cloud Run service is not ready: $service_status"
        return 1
    fi
    
    # Check if there are any running revisions
    local running_revisions=$(gcloud run revisions list --service="$SERVICE_NAME" --region="$REGION" --filter="status.conditions[0].status=True" --format="value(metadata.name)" 2>/dev/null | wc -l)
    if [[ $running_revisions -eq 0 ]]; then
        alert "No running Cloud Run revisions found"
        return 1
    fi
    
    log "Cloud Run status: OK ($running_revisions revision(s) running)"
    return 0
}

check_health_endpoint() {
    log "Checking health endpoint..."
    
    # Get the service URL
    local service_url=$(get_service_url)
    if [[ -z "$service_url" ]]; then
        alert "Cannot determine Cloud Run service URL"
        return 1
    fi
    
    # Test health endpoint
    local health_url="$service_url/api/health"
    local response=$(curl -s -w "%{http_code}" --max-time 10 "$health_url" 2>/dev/null)
    local http_code="${response: -3}"
    local body="${response%???}"
    
    if [[ $http_code -eq 200 ]]; then
        # Parse health status
        local status=$(echo "$body" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        if [[ "$status" == "healthy" ]]; then
            log "Health endpoint: OK (Status: $status)"
            return 0
        else
            alert "Health endpoint returned degraded status: $status"
            return 1
        fi
    else
        alert "Health endpoint failed with HTTP $http_code"
        return 1
    fi
}

check_dns_resolution() {
    log "Checking DNS resolution capability..."
    
    # Test DNS resolution using the app's own endpoint
    local service_url=$(get_service_url)
    if [[ -z "$service_url" ]]; then
        alert "Cannot determine Cloud Run service URL for DNS test"
        return 1
    fi
    
    # Test with a simple domain
    local test_url="$service_url/api/check?domain=google.com"
    local response=$(curl -s -w "%{http_code}" --max-time 15 "$test_url" 2>/dev/null)
    local http_code="${response: -3}"
    
    if [[ $http_code -eq 200 ]]; then
        log "DNS resolution: OK"
        return 0
    else
        alert "DNS resolution test failed with HTTP $http_code"
        return 1
    fi
}

check_database_connectivity() {
    log "Checking database connectivity..."
    
    # Test Firestore connectivity through the app
    local service_url=$(get_service_url)
    if [[ -z "$service_url" ]]; then
        alert "Cannot determine Cloud Run service URL for database test"
        return 1
    fi
    
    # Test with a domain that should trigger database storage
    local test_url="$service_url/api/check?domain=test-monitoring.com"
    local response=$(curl -s -w "%{http_code}" --max-time 20 "$test_url" 2>/dev/null)
    local http_code="${response: -3}"
    
    if [[ $http_code -eq 200 ]]; then
        log "Database connectivity: OK"
        return 0
    else
        alert "Database connectivity test failed with HTTP $http_code"
        return 1
    fi
}

check_resource_usage() {
    log "Checking resource usage..."
    
    # Check Cloud Run resource usage
    local instances=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.observedGeneration)" 2>/dev/null)
    local max_instances=10  # Based on deployment configuration
    
    # Check if instances are responding
    local responding_instances=0
    for i in {1..3}; do
        if check_health_endpoint >/dev/null 2>&1; then
            ((responding_instances++))
        fi
        sleep 1
    done
    
    if [[ $responding_instances -eq 0 ]]; then
        alert "No instances responding to health checks"
        return 1
    fi
    
    log "Resource usage: OK ($responding_instances responding)"
    return 0
}

check_error_logs() {
    log "Checking error logs..."
    
    # Get recent error logs from Cloud Run
    local error_count=$(gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND severity>=ERROR" --limit=50 --format="value(severity)" 2>/dev/null | wc -l)
    
    if [[ $error_count -gt 10 ]]; then
        alert "High error rate detected: $error_count errors in recent logs"
        return 1
    fi
    
    log "Error logs: OK ($error_count recent errors)"
    return 0
}

check_revision_health() {
    log "Checking revision health..."
    
    # Get current revision
    local current_revision=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.latestReadyRevisionName)" 2>/dev/null)
    
    if [[ -z "$current_revision" ]]; then
        alert "No ready revision found"
        return 1
    fi
    
    # Check revision status
    local revision_status=$(gcloud run revisions describe "$current_revision" --region="$REGION" --format="value(status.conditions[0].status)" 2>/dev/null)
    
    if [[ "$revision_status" != "True" ]]; then
        alert "Current revision is not ready: $revision_status"
        return 1
    fi
    
    log "Revision health: OK (Current: $current_revision)"
    return 0
}

perform_comprehensive_check() {
    local all_passed=true
    
    log "Starting comprehensive Cloud Run production check..."
    
    # Check Cloud Run status
    if ! check_cloud_run_status; then
        all_passed=false
    fi
    
    # Check revision health
    if ! check_revision_health; then
        all_passed=false
    fi
    
    # Check health endpoint
    if ! check_health_endpoint; then
        all_passed=false
    fi
    
    # Check DNS resolution
    if ! check_dns_resolution; then
        all_passed=false
    fi
    
    # Check database connectivity
    if ! check_database_connectivity; then
        all_passed=false
    fi
    
    # Check resource usage
    if ! check_resource_usage; then
        all_passed=false
    fi
    
    # Check error logs
    if ! check_error_logs; then
        all_passed=false
    fi
    
    if [[ "$all_passed" == "true" ]]; then
        log "All Cloud Run production checks passed"
        failure_count=0
        return 0
    else
        ((failure_count++))
        log "Cloud Run production check failed (consecutive failures: $failure_count)"
        
        if [[ $failure_count -ge $ALERT_THRESHOLD ]]; then
            alert "Cloud Run production environment issues detected after $failure_count consecutive failures"
        fi
        
        return 1
    fi
}

auto_recovery() {
    log "Attempting automatic recovery..."
    
    # Check if we need to restart the service
    if [[ $failure_count -ge 5 ]]; then
        log "Attempting service restart..."
        
        # Get current revision
        local current_revision=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.latestReadyRevisionName)" 2>/dev/null)
        
        if [[ -n "$current_revision" ]]; then
            # Update traffic to current revision (this can trigger a restart)
            if gcloud run services update-traffic "$SERVICE_NAME" --region="$REGION" --to-revisions="$current_revision=100" --quiet 2>/dev/null; then
                log "Service restart successful"
                failure_count=0
                return 0
            else
                alert "Service restart failed"
                return 1
            fi
        else
            alert "Cannot determine current revision for restart"
            return 1
        fi
    fi
    
    return 1
}

main() {
    log "Starting AstraVerify Cloud Run Production Monitor"
    log "Project: $PROJECT_ID"
    log "Service: $SERVICE_NAME"
    log "Region: $REGION"
    log "Monitor interval: ${MONITOR_INTERVAL}s"
    log "Alert threshold: $ALERT_THRESHOLD consecutive failures"
    log "Log file: $LOG_FILE"
    log "Alert log: $ALERT_LOG"
    
    # Ensure we're authenticated and in the right project
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        alert "Not authenticated with gcloud"
        exit 1
    fi
    
    if [[ "$(gcloud config get-value project 2>/dev/null)" != "$PROJECT_ID" ]]; then
        alert "Project not set to $PROJECT_ID"
        exit 1
    fi
    
    log "Authentication and project configuration verified"
    
    # Main monitoring loop
    while true; do
        if ! perform_comprehensive_check; then
            # Try automatic recovery
            if ! auto_recovery; then
                log "Automatic recovery failed, continuing monitoring"
            fi
        fi
        
        log "Waiting ${MONITOR_INTERVAL} seconds until next check..."
        sleep $MONITOR_INTERVAL
    done
}

# Handle script termination
trap 'log "Cloud Run production monitor stopped"; exit 0' SIGINT SIGTERM

# Run main function
main "$@"
