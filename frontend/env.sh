#!/bin/sh

# Replace environment variables in built React app
# This allows runtime configuration of environment variables

echo "Setting up environment variables..."

# Define the file to be modified
TARGET_FILE="/usr/share/nginx/html/static/js/main.*.js"

# Replace environment variable placeholders with actual values
if [ -n "$REACT_APP_BACKEND_URL" ]; then
    echo "Setting REACT_APP_BACKEND_URL to $REACT_APP_BACKEND_URL"
    find /usr/share/nginx/html -name "*.js" -type f -exec sed -i "s|REACT_APP_BACKEND_URL_PLACEHOLDER|$REACT_APP_BACKEND_URL|g" {} +
fi

echo "Environment variables setup complete."