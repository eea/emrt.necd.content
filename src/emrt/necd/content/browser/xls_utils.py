from itertools import takewhile


def clean_value(value):
    result = value

    # sometimes newlines from Excel are read as _x000D_\n, remove the _x000D_
    try:
        result = value.replace("_x000D_", "")
    except:
        pass

    return result


def get_valid_sheet_rows(sheet):
    sheet_rows = sheet.rows
    next(sheet_rows)  # skip first row (header)
    # extract rows with values
    valid_rows = tuple(
        takewhile(lambda row: any(c.value for c in row), sheet_rows)
    )
    return valid_rows
