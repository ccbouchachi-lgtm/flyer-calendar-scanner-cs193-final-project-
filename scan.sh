#!/bin/bash

echo "Enter flyer image path:"
read -r file

if [ -f "$file" ]; then
    echo "Processing image..."

    if .venv/bin/python scanner.py "$file"; then
        echo "Event extracted successfully!"
    else
        echo "Event extraction failed."
        exit 1
    fi

else
    echo "File not found."
    exit 1
fi