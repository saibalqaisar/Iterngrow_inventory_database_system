"""validators.py - safe input helpers. Each keeps asking until the input is valid."""

import getpass


def get_text(prompt, max_length=100):
    while True:
        value = input(prompt).strip()
        if not value:
            print("  Error: this field cannot be empty.")
        elif len(value) > max_length:
            print(f"  Error: maximum {max_length} characters.")
        else:
            return value


def get_name(prompt):
    """Names may contain letters, spaces, dots, hyphens and apostrophes."""
    while True:
        value = input(prompt).strip()
        cleaned = value.replace(" ", "").replace(".", "").replace("-", "").replace("'", "")
        if value and cleaned.isalpha() and len(value) <= 60:
            return value.title()
        print("  Error: name must contain letters only.")


def get_int(prompt, minimum, maximum):
    while True:
        raw = input(prompt).strip()
        try:
            number = int(raw)
        except ValueError:
            print("  Error: please enter a whole number.")
            continue
        if minimum <= number <= maximum:
            return number
        print(f"  Error: number must be between {minimum} and {maximum}.")


def get_float(prompt, minimum, maximum):
    while True:
        raw = input(prompt).strip()
        try:
            number = float(raw)
        except ValueError:
            print("  Error: please enter a number.")
            continue
        if minimum <= number <= maximum:
            return round(number, 2)
        print(f"  Error: number must be between {minimum} and {maximum}.")


def get_optional_int(prompt, minimum, maximum):
    """Press Enter to skip (returns None)."""
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return None
        try:
            number = int(raw)
        except ValueError:
            print("  Error: please enter a whole number, or press Enter to skip.")
            continue
        if minimum <= number <= maximum:
            return number
        print(f"  Error: number must be between {minimum} and {maximum}.")


def get_optional_float(prompt, minimum, maximum):
    """Press Enter to skip (returns None)."""
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return None
        try:
            number = float(raw)
        except ValueError:
            print("  Error: please enter a number, or press Enter to skip.")
            continue
        if minimum <= number <= maximum:
            return round(number, 2)
        print(f"  Error: number must be between {minimum} and {maximum}.")


def get_yes_no(prompt):
    while True:
        answer = input(prompt).strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Error: type y or n.")


def get_password(prompt):
    """Ask for a password without showing it on screen."""
    try:
        return getpass.getpass(prompt)
    except (EOFError, KeyboardInterrupt):
        raise
    except Exception:
        # Some consoles cannot hide typing; fall back to normal input.
        return input(prompt)
