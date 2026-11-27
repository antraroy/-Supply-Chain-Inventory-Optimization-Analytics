# ============================================================
# FIND COLUMN HELPER
# ============================================================

def find_column(df, possible_names):

    if df is None or df.empty:
        return None

    columns = {
        str(col).strip().lower(): col
        for col in df.columns
    }

    # Exact match
    for name in possible_names:

        name = str(name).strip().lower()

        if name in columns:
            return columns[name]

    # Partial match
    for col in df.columns:

        col_lower = str(col).strip().lower()

        for name in possible_names:

            if str(name).strip().lower() in col_lower:
                return col

    return None
