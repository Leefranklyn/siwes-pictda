"""This program is a simple number guessing game where the user has to guess a 
randomly selected number between 1 and 100 within a limited number of attempts."""

import random

def guess_number():
    """Function to generate a random number and 
    allow the user to guess it within a limited number of attempts."""

    number_to_guess = random.randint(1, 100)
    attempts = 0
    max_attempts = 5

    print("Number Guessing Game!")
    print(f"You have {max_attempts} attempts to guess the number.")

    while attempts < max_attempts:
        try:
            guess = int(input("Enter your guess: "))
            attempts += 1

            if guess < 1 or guess > 100:
                print("Please enter a number between 1 and 100.")
                continue

            if guess < number_to_guess:
                print("Too low! Try again.")
            elif guess > number_to_guess:
                print("Too high! Try again.")
            else:
                print(f"Congratulations! You've guessed the number {number_to_guess} in {attempts} attempts.")
                break
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

    if attempts == max_attempts and guess != number_to_guess:
        print(f"Sorry, you've used all your attempts. The number was {number_to_guess}.")


guess_number()
