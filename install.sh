#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Running this script will install the 'steg' command to /usr/local/bin by creating a symlink from there to the steg.py in THIS folder."
echo "You can try this command before installing it by running './steg.py' or 'python steg.py'"
read -p "Are you sure you want to install? " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Not installed."
    [[ "$0" = "$BASH_SOURCE" ]] && exit 1 || return 1
else
    echo "Installing..."
    chmod +x steg.py
    ln -s $DIR/steg.py /usr/local/bin/steg
    echo "Done."
fi
