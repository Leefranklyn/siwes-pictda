"""
This program simulates a simple employee payroll system using a class.
It stores an employee's name, salary, tax, and bonus, and calculates
their gross salary and net salary.
"""


class Employee:
    """Represent an employee and their payroll information."""

    def __init__(self, name, salary, tax, bonus):
        self.name = name
        self.salary = salary
        self.tax = tax
        self.bonus = bonus

    def gross_salary(self):
        """Calculate and return the employee's gross salary."""
        return self.salary + self.bonus

    def calculate_tax(self):
        """Calculate and return the tax deducted from the gross salary."""
        return self.gross_salary() * (self.tax / 100)

    def net_salary(self):
        """Calculate and return the employee's net salary."""
        return self.gross_salary() - self.calculate_tax()

    def display_payroll(self):
        """Display the employee's payroll information."""
        print(f"\nEmployee Name: {self.name}")
        print(f"Gross Salary: {self.gross_salary():.2f}")
        print(f"Tax: {self.calculate_tax():.2f}")
        print(f"Net Salary: {self.net_salary():.2f}")


def get_number(prompt):
    """Get a valid numerical value from the user."""
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def main():
    """Create an employee and display their payroll information."""
    name = input("Enter Employee Name: ")

    salary = get_number("Enter Salary: ")
    tax = get_number("Enter Tax (%): ")
    bonus = get_number("Enter Bonus: ")

    employee = Employee(name, salary, tax, bonus)

    employee.display_payroll()


main()
