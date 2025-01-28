
def validate_type(expected_type):
    def decorator(func):
        def wrapper(self, value):
            if not isinstance(value, expected_type):
                raise TypeError(f"Expected a value of type {expected_type.__name__}, got {type(value).__name__}.")
            return func(self, value)
        return wrapper
    return decorator