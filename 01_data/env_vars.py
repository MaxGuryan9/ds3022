import os

# --- SET environment variables ---
os.environ["COURSE_NAME"] = "DS3022"
os.environ["SEMESTER"] = "Fall2026"

# --- GET environment variables ---
course_name = os.environ.get("COURSE_NAME")
semester = os.environ.get("SEMESTER")

print("COURSE_NAME:", course_name, type(course_name))
print("SEMESTER:", semester, type(semester))

# --- INPUT examples ---
student_name = input("Enter your name: ")
favorite_number = input("Enter your favorite number: ")

print("Name:", student_name, type(student_name))
print("Favorite number:", favorite_number, type(favorite_number))
