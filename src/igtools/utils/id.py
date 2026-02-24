import sys

from math import ceil, log
from os import urandom
from abc import ABC, abstractmethod


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


def create_generator(config, existing_keys=None):
    if config.key_mode == "sequential":
        return SequentialIdGenerator(config=config, existing_keys=existing_keys)
    return RandomIdGenerator(config=config)


class IdGenerator(ABC):

    @abstractmethod
    def generate(self):
        pass


class RandomIdGenerator(IdGenerator):

    def __init__(self, config):
        self.prefix = f"{config.prefix}{config.separator}"
        self.scope = config.scope or ""

    def generate(self):
        _id = generate_id(
            prefix=self.prefix,
            scope=self.scope,
        )
        add_id(id=_id)
        return _id


class SequentialIdGenerator(IdGenerator):
    """Deterministic, config-aware requirement id generator.

    Starts after the highest numeric suffix found for the configured prefix/scope
    combination or a persisted counter from config (current_req_number), whichever
    is larger. Existing keys that do not match the sequential pattern are
    ignored so random ids remain untouched.
    """

    def __init__(self, config, existing_keys=None):
        self.config = config
        self.prefix = f"{self.config.prefix}{self.config.separator}"
        self.scope = self.config.scope or ""
        self.base = f"{self.prefix}{self.scope}"
        self.seen = {key for key in (existing_keys or []) if key}
        start_from_config = getattr(self.config, "current_req_number", 0) or 0
        self.counter = self._init_counter(config_next=start_from_config)

    def _init_counter(self, config_next=0):
        max_number = config_next
        for key in self.seen:
            if not key or not key.startswith(self.base):
                continue
            suffix = key[len(self.base):]
            if suffix.isdigit():
                try:
                    max_number = max(max_number, int(suffix))
                except ValueError:
                    continue
        return max_number

    def generate(self):
        while True:
            self.counter += 1
            candidate = f"{self.base}{self.counter}"
            if not is_already_added(candidate):
                add_id(candidate)
                self.config.current_req_number = self.get_counter()
                return candidate

    def get_counter(self):
        return self.counter