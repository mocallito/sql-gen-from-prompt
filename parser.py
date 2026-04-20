import re

def parse_columns(file_path):
    tables = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Skip header lines until we reach the table
    for line in lines:
        parts = re.split(r'\s{2,}', line.strip())
        if len(parts) == 2 and parts[0] != "COLUMN_NAME":
            column, table = parts
            # Skip header and separator lines
            if column in ("COLUMN_NAME", "---------------"):
                continue
            if table in ("TABLE_NAME", "-----------"):
                continue
            tables.append((table,column))
    return tables

def debug_print(tables):
    print("Parsed columns by table:\n")
    for table, cols in tables.items():
        print(f"Table: {table}")
        for col in cols:
            print(f"  - {col}")
        print()

def read_foreign_keys(filename):
    """
    Reads a text file containing foreign key query output and returns
    a list of dictionaries with FromTable, FromColumn, ToTable, ToColumn, FK_Name.
    """
    results = []
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find the header line
    header_index = None
    for i, line in enumerate(lines):
        if line.strip().startswith("FromTable"):
            header_index = i
            break

    if header_index is None:
        raise ValueError("Header row not found in file")

    # Skip header and separator line
    data_lines = lines[header_index + 2:]

    for line in data_lines:
        line = line.strip()
        if not line or line.startswith("(("):  # skip empty lines and summary
            continue

        # Split by whitespace into 5 parts
        parts = line.split()
        if len(parts) < 5:
            continue

        # Reconstruct FK_Name (it may contain underscores)
        from_table, from_column, to_table, to_column = parts[:4]
        fk_name = " ".join(parts[4:])

        results.append({
            "FromTable": from_table,
            "FromColumn": from_column,
            "ToTable": to_table,
            "ToColumn": to_column,
            "FK_Name": fk_name
        })

    return results


def print_foreign_keys(fk_list):
    """
    Prints the list of foreign key dictionaries in a formatted table.
    """
    # Print header
    print(f"{'FromTable':<12} {'FromColumn':<15} {'ToTable':<12} {'ToColumn':<15} {'FK_Name'}")
    print("-" * 70)

    # Print each entry
    for fk in fk_list:
        print(f"{fk['FromTable']:<12} {fk['FromColumn']:<15} {fk['ToTable']:<12} {fk['ToColumn']:<15} {fk['FK_Name']}")

    print(f"\n({len(fk_list)} rows affected)")


# Example usage:
if __name__ == "__main__":
    fk_list = read_foreign_keys("foreign_keys.txt")  # use your existing reader
    print_foreign_keys(fk_list)
