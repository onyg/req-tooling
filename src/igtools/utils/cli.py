

BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
WHITE = "\033[37m"

RESET_ALL = "\033[0m"


def format_table_with_border(headers, rows, min_width=10):
    """
    :param headers: Liste von (value, style)-Tupeln für die Spaltenüberschriften
    :param rows: Liste von Listen mit (value, style)-Tupeln für die Datenzeilen
    :param min_width: Mindestbreite für jede einzelne Spalte
    :return: Formatierte Tabelle als String
    """
    def get_style(style):
        """
        :param style: Style-Dictionary oder None
        :return: Style-Dictionary mit Standardwerten
        """
        if not isinstance(style, dict):
            style = {}
        return {
            "colspan": style.get("colspan", 1),
            "italic": style.get("italic", False),
            "bold": style.get("bold", False)
        }

    def calculate_widths(headers, rows, min_width):
        """
        :return: Liste der Spaltenbreiten
        """
        col_widths = []
        for row in [headers] + rows:
            if row == "separator":
                continue
            idx = 0
            for value, style in row:
                style = get_style(style)
                colspan = style["colspan"]
                value_width = len(str(value))
                while len(col_widths) <= idx:
                    col_widths.append(min_width)
                col_widths[idx] = max(col_widths[idx], value_width, min_width)
                idx += colspan
        return col_widths

    def apply_text_style(text, style):
        """
        :param text: Der Text, der formatiert wird.
        :param style: Das Style-Dictionary.
        :return: Formatierter Text.
        """
        if style["italic"]:
            text = f"\x1b[3m{text}\x1b[0m"  # ANSI für italic
        if style["bold"]:
            text = f"\x1b[1m{text}\x1b[0m"  # ANSI für bold
        return text

    def format_row(row, col_widths):
        """
        :return: Formatierte Zeile als String
        """
        if row == "separator":
            return "├" + "┼".join("-" * (width + 2) for width in col_widths) + "┤"

        result = []
        idx = 0
        for value, style in row:
            style = get_style(style)
            colspan = style["colspan"]
            value = apply_text_style(str(value), style)

            width = sum(col_widths[idx:idx + colspan]) + (colspan - 1) * 3
            cell = f" {value:<{width}} "

            result.append("│" + cell)
            idx += colspan

        return "".join(result) + ("│" if row[-1][1].get("separator_right", True) else "")

    col_widths = calculate_widths(headers, rows, min_width)
    table = ["┌" + "─".join("─" * (width + 2) for width in col_widths) + "┐"]
    table.append(format_row(headers, col_widths))
    table.append("├" + "┬".join("─" * (width + 2) for width in col_widths) + "┤")
    for row in rows:
        table.append(format_row(row, col_widths))
    table.append("└" + "┴".join("─" * (width + 2) for width in col_widths) + "┘")
    return "\n".join(table)


def print_app_title(title):
    print(title)
    print_line()

def print_line():
    print(f"{YELLOW}{'─'*50}{RESET_ALL}")


def print_command_title(title):
    print(f"{GREEN}{title}{RESET_ALL}")
    print("")

def print_command_title_with_app_info(app, version, title):
    print(f"{app} (v{version}) - {GREEN}{title}{RESET_ALL}")

def print_command(text):
    print(f"{BLUE}{text}{RESET_ALL}")


def print_error(text):
    print(f"{RED}{text}{RESET_ALL}")


def confirm_action(prompt, auto_confirm=False):
    """
    :param prompt: The confirmation message to display.
    :param auto_confirm: If True, skips confirmation and returns True.
    :return: True if confirmed, False otherwise.
    """
    if auto_confirm:
        return True

    while True:
        choice = input(f"{prompt} [y/N]: ").strip().lower()
        if choice in ["y", "yes"]:
            return True
        elif choice in ["n", "no", ""]:
            return False
        else:
            print("Please respond with 'y' or 'n'.")