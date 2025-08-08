#!/bin/bash

echo "=========================================="
echo "  AstraVerify Cloud Run Logs Tailer"
echo "=========================================="
echo ""

# Colors for different log levels
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to colorize log levels
colorize_logs() {
    sed -E \
        -e "s/(ERROR|error)/${RED}\1${NC}/g" \
        -e "s/(WARNING|warning)/${YELLOW}\1${NC}/g" \
        -e "s/(INFO|info)/${GREEN}\1${NC}/g" \
        -e "s/(DEBUG|debug)/${BLUE}\1${NC}/g" \
        -e "s/(SMTP|smtp)/${PURPLE}\1${NC}/g" \
        -e "s/(EMAIL|email)/${CYAN}\1${NC}/g"
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -b, --backend     Tail backend logs only"
    echo "  -f, --frontend    Tail frontend logs only"
    echo "  -a, --all         Tail both backend and frontend logs (default)"
    echo "  -e, --error       Show only error logs"
    echo "  -w, --warning     Show warning and error logs"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Tail all logs"
    echo "  $0 -b                 # Tail backend logs only"
    echo "  $0 -f                 # Tail frontend logs only"
    echo "  $0 -e                 # Show only errors"
    echo "  $0 -b -e              # Show backend errors only"
    echo ""
}

# Default values
SERVICE="all"
LOG_LEVEL="all"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--backend)
            SERVICE="backend"
            shift
            ;;
        -f|--frontend)
            SERVICE="frontend"
            shift
            ;;
        -a|--all)
            SERVICE="all"
            shift
            ;;
        -e|--error)
            LOG_LEVEL="error"
            shift
            ;;
        -w|--warning)
            LOG_LEVEL="warning"
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

echo "🔍 Configuration:"
echo "  Service: $SERVICE"
echo "  Log Level: $LOG_LEVEL"
echo ""

# Build the log filter
if [ "$SERVICE" = "backend" ]; then
    LOG_FILTER="resource.type=cloud_run_revision AND resource.labels.service_name=astraverify-backend"
elif [ "$SERVICE" = "frontend" ]; then
    LOG_FILTER="resource.type=cloud_run_revision AND resource.labels.service_name=astraverify-frontend"
else
    LOG_FILTER="resource.type=cloud_run_revision AND (resource.labels.service_name=astraverify-backend OR resource.labels.service_name=astraverify-frontend)"
fi

# Add severity filter if specified
if [ "$LOG_LEVEL" = "error" ]; then
    LOG_FILTER="$LOG_FILTER AND severity>=ERROR"
elif [ "$LOG_LEVEL" = "warning" ]; then
    LOG_FILTER="$LOG_FILTER AND severity>=WARNING"
fi

echo "📡 Starting log tail..."
echo "  Filter: $LOG_FILTER"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

# Start tailing logs with colorization
gcloud beta logging tail "$LOG_FILTER" --format="table(timestamp,severity,resource.labels.service_name,textPayload)" | colorize_logs
