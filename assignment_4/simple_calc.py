"""This is a simple calculator program that performs
basic arithmetic operations on two numbers."""

def get_number(input_value):
    while True:
        try:
            return float(input(input_value))
        except ValueError:
            print("Invalid input. Please enter a valid number.")


num_one = get_number("Enter a number: ")
num_two = get_number("Enter a number: ")


def calculate(num1, num2):
    addition = num1 + num2
    subtraction = num1 - num2
    multiplication = num1 * num2
    division = num1 / num2 if num2 != 0 else "undefined (division by zero)"
    modulus = num1 % num2 if num2 != 0 else "undefined (division by zero)"
    power = num1 ** num2

    return addition, subtraction, multiplication, division, modulus, power


addition, subtraction, multiplication, division, modulus, power = calculate(num_one, num_two)


print("*" * 20)
print("SIMPLE CALCULATOR")
print("*" * 20)
print(f"\nAddition: {addition}")
print(f"Subtraction: {subtraction}")
print(f"Multiplication: {multiplication}")
print(f"Division: {division}")
print(f"Modulus: {modulus}")
print(f"Power: {power}")

num3 = '23'
