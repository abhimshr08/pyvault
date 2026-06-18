import secrets
import string

def generate_password(length=12):
    if length < 4:
        length = 4
    # Guarantee at least one of each required character type
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice(string.punctuation)
    ]
    # Fill the rest of the length randomly
    characters = string.ascii_letters + string.digits + string.punctuation
    password += [secrets.choice(characters) for _ in range(length - 4)]
    # Shuffle to ensure the characters are not in a predictable order
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)