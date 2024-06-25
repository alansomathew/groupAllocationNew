import random

OTPdigits = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklnopqrstuvwxyz"

def generate_code(length=10):
    return ''.join(random.choice(OTPdigits) for _ in range(length))
