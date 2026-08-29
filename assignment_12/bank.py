"""
This program simulates a simple banking application where users can
create an account, deposit money, withdraw money, check their balance,
and transfer money between accounts.
"""

accounts = []


def create_account():
    """Create a new bank account and add it to the accounts list."""
    name = input("Enter your name: ")
    account_number = input("Enter account number: ")

    account = {
        "Name": name,
        "Account Number": account_number,
        "Balance": 0
    }

    accounts.append(account)

    print("Account created successfully.")


def check_balance():
    """Display the balance of a selected account."""
    account_number = input("Enter your account number: ")

    for account in accounts:
        if account["Account Number"] == account_number:
            print(f"Your current balance is: {account['Balance']:.2f}")
            return

    print("Account not found.")


def deposit():
    """Deposit money into an account."""
    account_number = input("Enter your account number: ")

    for account in accounts:
        if account["Account Number"] == account_number:

            while True:
                try:
                    amount = float(input("Enter the amount to deposit: "))

                    if amount <= 0:
                        print(
                            "Deposit amount cannot be zero or negative. "
                            "Please enter a valid amount."
                        )
                    else:
                        account["Balance"] += amount
                        print(
                            f"Successfully deposited {amount:.2f}. "
                            f"New balance is: {account['Balance']:.2f}"
                        )
                        return

                except ValueError:
                    print("Invalid input. Please enter a valid number.")

            return

    print("Account not found.")


def withdraw():
    """Withdraw money from an account."""
    account_number = input("Enter your account number: ")

    for account in accounts:
        if account["Account Number"] == account_number:

            while True:
                try:
                    amount = float(input("Enter the amount to withdraw: "))

                    if amount <= 0:
                        print(
                            "Withdrawal amount cannot be zero or negative. "
                            "Please enter a valid amount."
                        )
                    elif amount > account["Balance"]:
                        print("Insufficient funds. Please enter a smaller amount.")
                    else:
                        account["Balance"] -= amount
                        print(
                            f"Successfully withdrew {amount:.2f}. "
                            f"New balance is: {account['Balance']:.2f}"
                        )
                        return

                except ValueError:
                    print("Invalid input. Please enter a valid number.")

            return

    print("Account not found.")


def transfer():
    """Transfer money from one account to another."""
    sender_number = input("Enter your account number: ")
    receiver_number = input("Enter recipient account number: ")

    sender = None
    receiver = None

    for account in accounts:
        if account["Account Number"] == sender_number:
            sender = account

        if account["Account Number"] == receiver_number:
            receiver = account

    if sender is None:
        print("Sender account not found.")
        return

    if receiver is None:
        print("Recipient account not found.")
        return

    if sender_number == receiver_number:
        print("You cannot transfer money to the same account.")
        return

    while True:
        try:
            amount = float(input("Enter the amount to transfer: "))

            if amount <= 0:
                print(
                    "Transfer amount cannot be zero or negative. "
                    "Please enter a valid amount."
                )
            elif amount > sender["Balance"]:
                print("Insufficient funds. Please enter a smaller amount.")
            else:
                sender["Balance"] -= amount
                receiver["Balance"] += amount

                print(
                    f"Successfully transferred {amount:.2f} "
                    f"to account {receiver_number}."
                )
                print(f"Your new balance is: {sender['Balance']:.2f}")
                return

        except ValueError:
            print("Invalid input. Please enter a valid number.")


def main():
    """Run the main banking application menu."""
    while True:
        print("\n" + "*" * 20)
        print("Welcome to the Banking Application")
        print("*" * 20)

        print("\n1. Create Account")
        print("2. Check Balance")
        print("3. Deposit")
        print("4. Withdraw")
        print("5. Transfer")
        print("6. Exit")

        choice = input("Please select an option (1-6): ")

        if choice == "1":
            create_account()

        elif choice == "2":
            check_balance()

        elif choice == "3":
            deposit()

        elif choice == "4":
            withdraw()

        elif choice == "5":
            transfer()

        elif choice == "6":
            print("Thank you for using the Banking Application. Goodbye!")
            break

        else:
            print("Invalid selection. Please choose a valid option.")


main()
