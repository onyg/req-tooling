import os
import re


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
    if value:
        if isinstance(value, list):
            return value
        if isinstance(value, set):
            return list(value)
        elif isinstance(value, str):
            return [item.strip() for item in value.split(",")]
        return [value]
    return []


def distinct_list(value):
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"Expected a value of type list, got {type(value).__name__}.")
    return list(set(value))


def clean_list(value):
    if not isinstance(value, list):
        raise TypeError(f"Expected a value of type list, got {type(value).__name__}.")
    return list(filter(lambda x: x and x.strip(), distinct_list(value)))


def convert_to_link(source, key=None, version=None):
    filename = os.path.basename(source)
    if filename.endswith((".md", ".xml")):
        filename = filename.rsplit(".", 1)[0] + ".html"
    anchor = f"#{key}" if key else ""
    if anchor and version is not None:
        try:
            v_int = int(str(version).strip())
        except (ValueError, TypeError):
            v_int = None
        if v_int is not None and v_int > 0:
            anchor += f"-{v_int:02d}"
    return f"{filename}{anchor}"


def convert_to_ig_requirement_link(base, source, key, version):
    return f"{base}/{convert_to_link(source=source, key=key, version=version)}"


def clean_text(text):
    if text is None:
        return ""
    # 1) Newlines vereinheitlichen
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # 2) Nur normale Spaces am Anfang/Ende entfernen (keine anderen Whitespaces)
    text = text.strip(" ")
    # 3) Doppelte/mehrfache Spaces im Text zu einem Space machen
    text = re.sub(r" {2,}", " ", text)
    return text
