#!/bin/bash

# Start services
service postgresql start
service apache2 start

# Change to AutoSploit directory
cd AutoSploit/

# Set permissions
chmod +x autosploit.py

# Run AutoSploit with Python 3
python3 autosploit.py