"""
This program creates a simple contact book using a list of
dictionaries. Users can add, search, delete, and view contacts.
"""

contacts = []


def add_contact():
    """Add a new contact to the contact book."""
    contact = {
        "Name": input("Enter Contact Name: "),
        "Phone": input("Enter Phone Number: "),
        "Email": input("Enter Email: ")
    }

    contacts.append(contact)
    print("Contact Added Successfully")


def search_contact():
    """Search for a contact by name and display their information."""
    name = input("Enter Contact Name: ")

    for index, contact in enumerate(contacts):
        if contact["Name"].lower() == name.lower():
            print(contacts[index])
            return

    print("Contact not found.")


def delete_contact():
    """Search for a contact by name and delete the matching contact."""
    name = input("Enter Contact Name: ")

    for index, contact in enumerate(contacts):
        if contact["Name"].lower() == name.lower():
            deleted_contact = contacts.pop(index)
            print(f"{deleted_contact['Name']} deleted successfully.")
            return

    print("Contact not found.")


def view_contacts():
    """Display all contacts in the contact book."""
    if not contacts:
        print("No contacts found.")
        return

    print("\n===== Contacts =====")

    for index, contact in enumerate(contacts):
        print(f"{index}. {contact}")


def main():
    """Run the contact book menu."""
    while True:
        print("\n===== Contact Book =====")
        print("1. Add Contact")
        print("2. Search Contact")
        print("3. Delete Contact")
        print("4. View Contacts")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            add_contact()

        elif choice == "2":
            search_contact()

        elif choice == "3":
            delete_contact()

        elif choice == "4":
            view_contacts()

        elif choice == "5":
            print("Exiting Contact Book...")
            break

        else:
            print("Invalid option. Please select 1-5.")


main()
