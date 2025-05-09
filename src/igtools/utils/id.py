import sys

from math import ceil, log
from os import urandom


# ALPHA = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
ALPHA = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
DIGITS = '0123456789'
CHAR_SET = DIGITS + ALPHA

current_ids = set()


def is_already_added(id):
    return id in current_ids


def add_id(id):
    if not is_already_added(id=id):
        current_ids.add(id)
        return True
    return False


def create_id(length, charset):
    charset_length = len(charset)

    bitmask = 1
    if charset_length > 1:
        bitmask = (2 << int(log(charset_length - 1) / log(2))) - 1
    steps = int(ceil(1.6 * bitmask * length / charset_length))

    identifier = ''
    while True:
        random_data = bytearray(urandom(steps))

        for i in range(steps):
            masked_byte = random_data[i] & bitmask
            if masked_byte < charset_length:
                if charset[masked_byte]:
                    identifier += charset[masked_byte]

                    if len(identifier) == length:
                        return identifier


def generate_id(prefix=None, scope=None):
    while True:
        numeric_segment = create_id(length=5, charset=DIGITS)
        alpha_segment = create_id(length=1, charset=ALPHA)
        alpha_num_segment = create_id(length=2, charset=CHAR_SET)
        _id = f"{prefix or ''}{scope or ''}{numeric_segment}{alpha_segment}{alpha_num_segment}"
        if add_id(id=_id):
            return _id