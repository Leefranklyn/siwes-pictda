"""
This program manages student information using a text file.
Users can create a student file, add students, save students,
read students from the file, and delete students.
"""

FILE_NAME = "students.txt"

students = []


def create_file():
    """Create the students.txt file if it does not already exist."""
    try:
        with open(FILE_NAME, "x", encoding="utf-8"):
            pass

        print("Student file created successfully.")

    except FileExistsError:
        print("Student file already exists.")


def load_students():
    """Load students from the file into the students list."""
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            students.clear()
            students.extend(student.strip() for student in file if student.strip())

    except FileNotFoundError:
        print("Student file does not exist. Create the file first.")


def add_student():
    """Add a student to the in-memory students list."""
    name = input("Enter Student Name: ").strip()

    if not name:
        print("Student name cannot be empty.")
        return

    students.append(name)

    print("Student Added Successfully")


def save_students():
    """Save all students from the list to the student file."""
    try:
        with open(FILE_NAME, "w", encoding="utf-8") as file:
            for student in students:
                file.write(student + "\n")

        print("Students saved successfully.")

    except FileNotFoundError:
        print("Student file does not exist. Create the file first.")


def read_students():
    """Read and display all students stored in the file."""
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            saved_students = file.readlines()

        if not saved_students:
            print("No students found.")
            return

        print("\n===== Students =====")

        for index, student in enumerate(saved_students):
            print(f"{index}. {student.strip()}")

    except FileNotFoundError:
        print("Student file does not exist. Create the file first.")


def delete_student():
    """Delete a student from the in-memory list and save the changes."""
    if not students:
        print("No students available.")
        return

    print("\n===== Students =====")

    for index, student in enumerate(students):
        print(f"{index}. {student}")

    try:
        index = int(input("Enter the index of the student to delete: "))

        if 0 <= index < len(students):
            deleted_student = students.pop(index)

            print(f"{deleted_student} deleted successfully.")

            save_students()

        else:
            print("Invalid index.")

    except ValueError:
        print("Please enter a valid number.")


def main():
    """Run the student file management menu."""
    load_students()

    while True:
        print("\n===== Student File Management =====")
        print("1. Create File")
        print("2. Add Student")
        print("3. Save Students")
        print("4. Read Students")
        print("5. Delete Student")
        print("6. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            create_file()

        elif choice == "2":
            add_student()

        elif choice == "3":
            save_students()

        elif choice == "4":
            read_students()

        elif choice == "5":
            delete_student()

        elif choice == "6":
            print("Exiting Student File Management...")
            break

        else:
            print("Invalid option. Please select 1-6.")


main()
