#! /bin/bash

# This script is used as a temporary no-config way of lauching TaiiCMS. It's
# useful for debugging and development, but it's really not for production.
# It's insecure and quite slow. It's reccommended that you serve these scripts
# separately by configuring a production webserver like Apache or nGinX.

trap "kill %1" SIGINT

python3 main.py
