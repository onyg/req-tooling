from .cli import print_error, print_info, print_warning


class ToolLogger:

    def __init__(self):
        pass

    def info(self, text):
        print_info(f"INFO: {text}")

    def warning(self, text):
        print_warning(f"WARNING: {text}")

    def error(self, text):
        print_error(f"ERROR: {text}")


log = ToolLogger()
    