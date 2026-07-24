"""This program checks the result of a student based on their score."""

name = input("Enter Student Name: ")

# Runs a loop to ensure the user enters a valid score between 0 and 100
while True:
    try:
        score = float(input("Enter Score: "))
        if 0 <= score <= 100:
            break
        else:
            print("Score must be a value between 0 and 100")
    except ValueError:
        print("Enter a Valid Score")


# Function to check the result based on the score
def checkResult(mark):
    if 70 <= mark <= 100:
        return f'Excellent - {mark}'
    elif 60 <= mark <= 69:
        return f'Very Good - {mark}'
    elif 50 <= mark <= 59:
        return f'Good - {mark}'
    elif 45 <= mark <= 49:
        return f'Pass - {mark}'
    elif 40 <= mark <= 44:
        return f'Pass - {mark}'
    else:
        return f'Fail - {mark}'


result = checkResult(score)
bonus = "Congratulations" if 40 <= score <= 44 else "Better Luck Next Time"

print("*" * 20)
print("Student Result Checker")
print("*" * 20)
print(name)
print(bonus)
print(result)