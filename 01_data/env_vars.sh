#!/bin/bash

# --- SET environment variables ---
export COURSE_NAME="DS3022"
export SEMESTER="Fall2026"

# --- GET environment variables ---
echo "COURSE_NAME: $COURSE_NAME"
echo "SEMESTER: $SEMESTER"

# --- Solicit user input ---
read -p "Enter your name: " student_name
read -p "Enter your favorite number: " favorite_number
read -p "Enter your favorite class: " favorite_class

# --- Display inputs back ---
echo "Name: $student_name"
echo "Favorite number: $favorite_number"
echo "Favorite class: $favorite_class"
