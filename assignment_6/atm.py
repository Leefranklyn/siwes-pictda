"""This program simulates a simple ATM system where users can check their balance, deposit money, and withdraw money."""


# function to check the current balance of the account
def check_balance(balance):
    print(f"Your current balance is: {balance:.2f}")


# function to deposit money into the account
def deposit(balance):
    while True:
        try:
            amount = float(input("Enter the amount to deposit: "))
            if amount <= 0:
                print("Deposit amount cannot be zero or negative. Please enter a valid amount.")
            else:
                balance += amount
                print(f"Successfully deposited {amount:.2f}. New balance is: {balance:.2f}")
                return balance
        except ValueError:
            print("Invalid input. Please enter a valid number.")


# function to withdraw money from the account
def withdraw(balance):
    while True:
        try:
            amount = float(input("Enter the amount to withdraw: "))
            if amount <= 0:
                print("Withdrawal amount cannot be zero or negative. Please enter a valid amount.")
            elif amount > balance:
                print("Insufficient funds. Please enter a smaller amount.")
            else:
                balance -= amount
                print(f"Successfully withdrew {amount:.2f}. New balance is: {balance:.2f}")
                return balance
        except ValueError:
            print("Invalid input. Please enter a valid number.")


# main entry point of the ATM program
def main():
    balance = 100000

    while True:
        print("*" * 20)
        print("Welcome to the ATM")
        print("*" * 20)
        print("\n1. Check Balance")
        print("2. Deposit Money")
        print("3. Withdraw Money")
        print("4. Exit")

        choice = input("Please select an option (1-4): ")

        if choice == '1':
            check_balance(balance)
        elif choice == '2':
            balance = deposit(balance)
        elif choice == '3':
            balance = withdraw(balance)
        elif choice == '4':
            print("Thank you for using the ATM. Goodbye!")
            break
        else:
            print("Invalid selection. Please choose a valid option.")


# main function call to start the ATM program
main()
