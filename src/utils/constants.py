import enum 
import string

ALPHABET = string.ascii_letters  # used by ID generator
ID_LENGTH = 26  # default length of IDs of all objects except for invoice
PUBLIC_ID_LENGTH = 22  # The length of invoice and products ids; should be shorter than usual for better UX
TOTP_LENGTH = 6  # for email verification and such
TOTP_ALPHABET = string.digits  # only numbers for ease of access
STR_TO_BOOL_MAPPING = {
    "true": True,
    "yes": True,
    "1": True,
    "false": False,
    "no": False,
    "0": False,
}  # common str -> bool conversions
TFA_RECOVERY_ALPHABET = "23456789BCDFGHJKMNPQRTVWXY".lower()  # avoid confusing chars
TFA_RECOVERY_LENGTH = 5  # each part has 5 chars