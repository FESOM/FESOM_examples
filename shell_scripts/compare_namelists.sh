#!/bin/bash

# Check if two arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <directory1> <directory2>"
    exit 1
fi

# Directories to compare
DIR1="$1"
DIR2="$2"

# Output file for the summary
OUTPUT_FILE="comparison_summary.txt"

# Check if output file already exists and remove it
[ -f "$OUTPUT_FILE" ] && rm "$OUTPUT_FILE"

# Function to compare files
compare_files() {
    local file1="$1"
    local file2="$2"
    local filename=$(basename "$file1")

    # Add header to the output file
    echo "Comparing $filename:" >> "$OUTPUT_FILE"
    echo "----------------------------------------" >> "$OUTPUT_FILE"

    # Compare the files and append the output to the file
    if [ -f "$file2" ]; then
        diff "$file1" "$file2" >> "$OUTPUT_FILE"
    else
        echo "WARNING: $filename does not exist in $(dirname "$file2")" >> "$OUTPUT_FILE"
    fi

    # Add a separator for readability
    echo "" >> "$OUTPUT_FILE"
    echo "----------------------------------------" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
}

# Compare files from DIR1 to DIR2
for file in "$DIR1"/namelist.*; do
    [ -e "$file" ] && compare_files "$file" "$DIR2/$(basename "$file")"
done

# Compare files from DIR2 to DIR1 (to catch files only in DIR2)
for file in "$DIR2"/namelist.*; do
    if [ -e "$file" ] && [ ! -e "$DIR1/$(basename "$file")" ]; then
        compare_files "$file" "$DIR1/$(basename "$file")"
    fi
done

# Display the summary
cat "$OUTPUT_FILE"
