"""
This program simulates a simple library management system.
Users can add, borrow, return, delete, and search for books.
"""


class Book:
    """Represent a book in the library."""

    def __init__(self, title, author):
        self.title = title
        self.author = author
        self.borrowed = False

    def __str__(self):
        """Return a readable representation of the book."""
        status = "Borrowed" if self.borrowed else "Available"
        return f"{self.title} by {self.author} - {status}"


class Library:
    """Manage books and borrowing operations."""

    def __init__(self):
        self.books = []
        self.borrowed = {}

    def add_book(self):
        """Add a new book to the library."""
        title = input("Enter Book Title: ")
        author = input("Enter Book Author: ")

        book = Book(title, author)
        self.books.append(book)

        print("Book Added Successfully")

    def borrow_book(self):
        """Borrow a book from the library."""
        title = input("Enter Book Title: ")

        for book in self.books:
            if book.title.lower() == title.lower():

                if book.borrowed:
                    print("Book is already borrowed.")
                    return

                borrower = input("Enter Borrower's Name: ")

                book.borrowed = True
                self.borrowed[book.title] = borrower

                print("Book Borrowed Successfully")
                return

        print("Book not found.")

    def return_book(self):
        """Return a borrowed book to the library."""
        title = input("Enter Book Title: ")

        for book in self.books:
            if book.title.lower() == title.lower():

                if not book.borrowed:
                    print("Book is not currently borrowed.")
                    return

                book.borrowed = False
                self.borrowed.pop(book.title, None)

                print("Book Returned Successfully")
                return

        print("Book not found.")

    def delete_book(self):
        """Delete a book from the library."""
        title = input("Enter Book Title: ")

        for index, book in enumerate(self.books):
            if book.title.lower() == title.lower():

                if book.borrowed:
                    print("Cannot delete a borrowed book.")
                    return

                self.books.pop(index)
                print("Book Deleted Successfully")
                return

        print("Book not found.")

    def search_book(self):
        """Search for a book by title."""
        title = input("Enter Book Title: ")

        for book in self.books:
            if title.lower() in book.title.lower():
                print(book)

        return

    def view_books(self):
        """Display all books in the library."""
        if not self.books:
            print("No books available.")
            return

        print("\n===== Books =====")

        for index, book in enumerate(self.books):
            print(f"{index}. {book}")


def main():
    """Run the library management system."""
    library = Library()

    while True:
        print("\n===== Library Management System =====")
        print("1. Add Book")
        print("2. Borrow Book")
        print("3. Return Book")
        print("4. Delete Book")
        print("5. Search Book")
        print("6. View Books")
        print("7. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            library.add_book()

        elif choice == "2":
            library.borrow_book()

        elif choice == "3":
            library.return_book()

        elif choice == "4":
            library.delete_book()

        elif choice == "5":
            library.search_book()

        elif choice == "6":
            library.view_books()

        elif choice == "7":
            print("Exiting Library Management System...")
            break

        else:
            print("Invalid option. Please select 1-7.")


main()
