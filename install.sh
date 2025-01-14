#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Clone the repository
git clone https://github.com/ngordon1git/HepaticRenalRatio.git
cd HepaticRenalRatio

# Create a virtual environment
python3 -m venv HRRGUI

# Activate the virtual environment
source HRRGUI/bin/activate

# Install prerequisites
pip install --upgrade pip
pip install -r requirements.txt

# Notify user of completion
echo "Setup is complete. The virtual environment is activated. Run your scripts as needed."
