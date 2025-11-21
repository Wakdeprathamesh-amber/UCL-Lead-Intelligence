#!/bin/bash
# Update VERSION.txt with current git commit hash and message
# This file is used by the Streamlit app to display deployment version

git rev-parse --short HEAD > VERSION.txt
git log -1 --pretty=format:"%s" >> VERSION.txt

