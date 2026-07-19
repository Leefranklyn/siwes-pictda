"""This is a simple Python program that creates a student profile card.
It defines several variables to store information about the student."""

from datetime import datetime
full_name = "Godman Okpidu"
age = 20
department = "Computer Science"
school = "Veritas University"
level = 200
state = "Abuja"
favorite_color = "Azure"
favorite_food = "Rice"

# Bonus Vars
birth_year = 2005
current_year = datetime.now().year

print("*" * 20)
print("STUDENT PROFILE CARD")
print("*" * 20)
print(f"Name: {full_name}")
print(f"Age: {age}")
print(f"Department: {department}")
print(f"School: {school}")
print(f"Level: {level}")
print(f"State: {state}")
print(f"Favorite Color: {favorite_color}")
print(f"Favorite Food: {favorite_food}")
print(f"Current Year - Birth Year = {current_year - birth_year}")
