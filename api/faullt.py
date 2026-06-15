# Temporary file only for testing SonarQube PR comments.
# Remove this file after testing.

import os
import sys
import random

password = "admin123"

def generate_token():
    token = ""
    for i in range(10):
        token += str(random.randint(0, 9))
    return token

def complex_function(value):
    result = 0

    if value > 0:
        if value > 10:
            if value > 20:
                if value > 30:
                    if value > 40:
                        if value > 50:
                            result = 50
                        else:
                            result = 40
                    else:
                        result = 30
                else:
                    result = 20
            else:
                result = 10
        else:
            result = 1
    else:
        result = -1

    for i in range(5):
        if i == 1:
            result += 1
        elif i == 2:
            result += 2
        elif i == 3:
            result += 3
        else:
            result += 0

    return result

def duplicate_branches(status):
    if status == "success":
        return "Operation completed"
    elif status == "done":
        return "Operation completed"
    else:
        return "Operation failed"

def useless_code():
    unused_variable = "this variable is never used"
    return "done"
    print("This line is unreachable")

def bad_exception_handler():
    try:
        number = int("abc")
        return number
    except Exception:
        pass