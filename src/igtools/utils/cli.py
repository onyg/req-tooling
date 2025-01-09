
def format_table_with_border(headers, rows, min_width=10):
    """
    :param headers: Liste von (value, style)-Tupeln für die Spaltenüberschriften
    :param rows: Liste von Listen mit (value, style)-Tupeln für die Datenzeilen
    :param min_width: Mindestbreite für jede einzelne Spalte
    :return: Formatierte Tabelle als String
    """
    def get_style(style):
        """
        Stellt sicher, dass das Style-Dictionary vorhanden ist, und setzt Standardwerte.
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
        Berechnet die Spaltenbreiten basierend auf den Headers, Rows und der Mindestbreite.
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
        Wendet Textstile (italic, bold) an.
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
        Formatiert eine Zeile basierend auf den Spaltenbreiten und Stilen.
        :return: Formatierte Zeile als String
        """
        if row == "separator":
            return "+" + "+".join("-" * (width + 2) for width in col_widths) + "+"

        result = []
        idx = 0
        for value, style in row:
            style = get_style(style)
            colspan = style["colspan"]
            value = apply_text_style(str(value), style)

            width = sum(col_widths[idx:idx + colspan]) + (colspan - 1) * 3
            cell = f" {value:<{width}} "

            result.append("|" + cell)
            idx += colspan

        return "".join(result) + ("|" if row[-1][1].get("separator_right", True) else "")

    col_widths = calculate_widths(headers, rows, min_width)
    table = ["+" + "+".join("-" * (width + 2) for width in col_widths) + "+"]
    table.append(format_row(headers, col_widths))
    table.append("+" + "+".join("-" * (width + 2) for width in col_widths) + "+")
    for row in rows:
        table.append(format_row(row, col_widths))
    table.append("+" + "+".join("-" * (width + 2) for width in col_widths) + "+")
    return "\n".join(table)

