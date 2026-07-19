"""This is a simple student registration program that collects basic 
information from the user."""

name = input("Enter your full name: ")
while True:
    try:
        age = int(input("Enter your age: "))
        break
    except ValueError:
        print("Invalid input. Please enter a valid age.")
department = input("Enter your department: ")
email = input("Enter your email address: ")
phone_number = input("Enter your phone number: ")
school = input("Enter your school name: ")

print("*" * 20)
print("STUDENT REGISTRATION")
print("*" * 20)
print("Welcome John.\nYou have Successfully registered.\n")
print(f"Department:\n{department}\n")
print(f"Email:\n{email}")
