"""
This program manages expenses using a text file. Users can add
expenses, view saved expenses, and calculate the total amount
of all expenses.
"""

FILE_NAME = "expenses.txt"


def add_expense():
    """Add an expense to the expense file."""
    description = input("Enter Expense Description: ").strip()

    if not description:
        print("Expense description cannot be empty.")
        return

    while True:
        try:
            amount = float(input("Enter Expense Amount: "))

            if amount <= 0:
                print("Expense amount must be greater than zero.")
                continue

            with open(FILE_NAME, "a", encoding="utf-8") as file:
                file.write(f"{description}:{amount}\n")

            print("Expense Added Successfully")
            break

        except ValueError:
            print("Invalid amount. Please enter a valid number.")


def view_expenses():
    """Read and display all expenses stored in the file."""
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            expenses = file.readlines()

        if not expenses:
            print("No expenses found.")
            return

        print("\n===== Expenses =====")

        for index, expense in enumerate(expenses):
            description, amount = expense.strip().split(":")

            print(f"{index}. {description} - {float(amount):.2f}")

    except FileNotFoundError:
        print("No expense file found.")


def calculate_total():
    """Calculate and display the total of all saved expenses."""
    total = 0

    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            expenses = file.readlines()

        if not expenses:
            print("No expenses found.")
            return

        for expense in expenses:
            description, amount = expense.strip().split(":")
            total += float(amount)

        print(f"Total Expenses: {total:.2f}")

    except FileNotFoundError:
        print("No expense file found.")


def main():
    """Run the expense tracker menu."""
    while True:
        print("\n===== Expense Tracker =====")
        print("1. Add Expense")
        print("2. View Expenses")
        print("3. Calculate Total")
        print("4. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            add_expense()

        elif choice == "2":
            view_expenses()

        elif choice == "3":
            calculate_total()

        elif choice == "4":
            print("Exiting Expense Tracker...")
            break

        else:
            print("Invalid option. Please select 1-4.")


main()