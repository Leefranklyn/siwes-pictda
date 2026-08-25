"""
This program is a simple Student Management System that uses a list
to store and manage student names. Users can add, remove, view, and
count students.
"""

import re


students = []


def add_student():
    """Add a new student to the student list."""
    name = input("Enter Student Name: ").strip()

    if name:
        students.append(name)
        print("Student Added Successfully")
    else:
        print("Student name cannot be empty.")


def remove_student():
    """Search for a student by name and remove the selected match."""
    if not students:
        print("There are no students to remove.")
        return

    search = input("Enter Student Name: ").strip()

    if not search:
        print("Search name cannot be empty.")
        return

    matches = []

    for index, student in enumerate(students):
        if re.search(re.escape(search), student, re.IGNORECASE):
            matches.append((index, student))

    if not matches:
        print("No matching students found.")
        return

    print("\nMatching Students:")

    for index, student in matches:
        print(f"Index: {index} | Name: {student}")

    try:
        index = int(input("Enter the index of the student to remove: "))

        if index in [match[0] for match in matches]:
            removed_student = students.pop(index)
            print(f"{removed_student} removed successfully.")
        else:
            print("Invalid index.")

    except ValueError:
        print("Please enter a valid number.")


def view_students():
    """Display all students currently stored in the student list."""
    if not students:
        print("No students have been added yet.")
        return

    print("\n===== Students =====")

    for index, student in enumerate(students):
        print(f"{index}. {student}")


def count_students():
    """Display the total number of students in the list."""
    print(f"Total Students: {len(students)}")


def main():
    """Run the main menu and handle user selections."""
    while True:
        print("\n===== Student Management System =====")
        print("1. Add Student")
        print("2. Remove Student")
        print("3. View Students")
        print("4. Count Students")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            add_student()

        elif choice == "2":
            remove_student()

        elif choice == "3":
            view_students()

        elif choice == "4":
            count_students()

        elif choice == "5":
            print("Exiting Student Management System...")
            break

        else:
            print("Invalid option. Please select 1-5.")


main()
