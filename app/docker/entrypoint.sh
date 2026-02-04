#!/bin/bash
set -e

# APP_KEY is provided via environment; avoid artisan usage here

# Run the command
exec "$@"
