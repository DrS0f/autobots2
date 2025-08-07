#!/bin/bash

# Wait for MongoDB to be ready before starting the backend service

set -e

host="mongo"
port="27017"
timeout=30
quiet=false

usage() {
    cat << USAGE >&2
Usage: $0 [OPTIONS] [--] COMMAND ARGS
    -h HOST         Host or IP under test (default: $host)
    -p PORT         TCP port under test (default: $port)  
    -t TIMEOUT      Timeout in seconds (default: $timeout)
    -q              Don't output any status messages
    --              End of options, start of command to execute
    
This script will wait for MongoDB to be ready before executing the given command.
USAGE
    exit 1
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -h)
            host="$2"
            shift 2
            ;;
        -p)
            port="$2"
            shift 2
            ;;
        -t)
            timeout="$2"
            shift 2
            ;;
        -q)
            quiet=true
            shift 1
            ;;
        --)
            shift
            break
            ;;
        -*)
            echo "Unknown option $1"
            usage
            ;;
        *)
            break
            ;;
    esac
done

wait_for_mongo() {
    if [[ $quiet != true ]]; then
        echo "Waiting for MongoDB at $host:$port..."
    fi

    start_time=$(date +%s)
    while ! mongosh --host "$host:$port" --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; do
        current_time=$(date +%s)
        if [[ $((current_time - start_time)) -gt $timeout ]]; then
            echo >&2 "Timeout occurred after waiting $timeout seconds for MongoDB at $host:$port"
            exit 1
        fi
        if [[ $quiet != true ]]; then
            echo "MongoDB is unavailable - sleeping..."
        fi
        sleep 2
    done

    if [[ $quiet != true ]]; then
        echo "MongoDB is up and running at $host:$port!"
    fi
}

# Check if mongosh is available, if not try to install it
if ! command -v mongosh &> /dev/null; then
    echo "mongosh not found, installing..."
    # For Alpine/Debian based images
    if command -v apk &> /dev/null; then
        apk add --no-cache mongodb-tools
    elif command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y mongodb-clients
    else
        echo "Could not install mongosh. Using basic connection test instead."
        # Fallback to basic connectivity test
        wait_for_basic_connection() {
            start_time=$(date +%s)
            while ! nc -z "$host" "$port"; do
                current_time=$(date +%s)
                if [[ $((current_time - start_time)) -gt $timeout ]]; then
                    echo >&2 "Timeout occurred after waiting $timeout seconds for $host:$port"
                    exit 1
                fi
                if [[ $quiet != true ]]; then
                    echo "MongoDB port is unavailable - sleeping..."
                fi
                sleep 2
            done
            if [[ $quiet != true ]]; then
                echo "MongoDB port is available at $host:$port!"
            fi
        }
        wait_for_basic_connection
    fi
else
    wait_for_mongo
fi

# Execute the provided command
if [[ $# -gt 0 ]]; then
    exec "$@"
fi