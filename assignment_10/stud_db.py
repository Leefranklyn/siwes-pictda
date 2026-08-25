"""
This program creates a simple student database using a list of
dictionaries. Each dictionary stores the information of one student.
"""

students = []


def add_student():
    """Add a student's information to the database."""
    student = {
        "Name": input("Enter Student Name: "),
        "Age": input("Enter Student Age: "),
        "Course": input("Enter Student Course: "),
        "Phone": input("Enter Student Phone: "),
        "Email": input("Enter Student Email: ")
    }

    students.append(student)
    print("Student Added Successfully")


def retrieve_student():
    """Search for a student by name and display their information."""
    name = input("Enter Student Name: ")

    for index, student in enumerate(students):
        if student["Name"].lower() == name.lower():
            print(students[index])
            return

    print("Student not found.")


def main():
    """Run the student database menu."""
    while True:
        print("\n===== Student Database =====")
        print("1. Add Student")
        print("2. Retrieve Information")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            add_student()

        elif choice == "2":
            retrieve_student()

        elif choice == "3":
            print("Exiting Student Database...")
            break

        else:
            print("Invalid option. Please select 1-3.")


main()
