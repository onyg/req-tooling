import os


def validate_type(expected_type):
    def decorator(func):
        def wrapper(self, value):
            if not isinstance(value, expected_type):
                raise TypeError(f"Expected a value of type {expected_type.__name__}, got {type(value).__name__}.")
            return func(self, value)
        return wrapper
    return decorator


def to_str(value):
    if isinstance(value, str):
        return value
    elif isinstance(value, list):
        return ", ".join(value)
    return f"{value}"


def to_list(value):
    if isinstance(value, list):
        return value
    elif isinstance(value, str):
        return [item.strip() for item in value.split(",")]
    return [value]


def distinct_list(value):
    if not isinstance(value, list):
        raise TypeError(f"Expected a value of type list, got {type(value).__name__}.")
    return list(set(value))


def clean_list(value):
    if not isinstance(value, list):
        raise TypeError(f"Expected a value of type list, got {type(value).__name__}.")
    return list(filter(lambda x: x and x.strip(), distinct_list(value)))


def convert_to_link(source, key=None, version=None):
    filename = os.path.basename(source)
    if filename.endswith(".md") or filename.endswith(".xml"):
        filename = filename.rsplit(".", 1)[0] + ".html"
    anchor = f"#{key}" if key else ""
    if anchor:
        if version and version > 1:
            anchor += f"-{version}"
    return f"{filename}{anchor}"