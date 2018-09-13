#!/usr/bin/env bash


if [ -f /etc/redhat-release ]; then
    virtualenv -p /usr/bin/python3 --no-site-packages venv
else
    pyenv install -s 3.6.4
    virtualenv -p ~/.pyenv/versions/3.6.4/bin/python --clear --always-copy --no-site-packages venv
fi

source venv/bin/activate
pip3 install -r requirements.txt
deactivate
