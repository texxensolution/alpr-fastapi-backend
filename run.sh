#!/bin/bash

if [[ "$(uname)" == "Linux" ]]; then
    echo "Operating system is linux!"
else
    echo "The operating system is not Linux."
    exit 1
fi

if command -v python3 &> /dev/null; then
    echo "Python is installed :)"
else
    echo "Python is not installed."
    sudo apt install python3 && python3-venv -y
fi

if [ -d ".venv" ]; then
    echo ".venv directory exist. Deleting it..."

    rm -rf .venv
    
    echo ".venv directory deleted."
else
    echo ".venv directory does not exist."

    python3 -m venv .venv

    echo "Virtual environment created at .venv folder! :)"

    echo "Activating virtual environment!"
    source .venv/bin/activate

    echo "installing python dependencies"
    python3 -m pip install -r requirements.txt

    echo "Python dependencies is all installed. Go on!"
fi

