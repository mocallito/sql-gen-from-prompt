import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def find_relation(relations, from_table, to_table):
    return [rel for rel in relations if rel["FromTable"] == from_table and rel["ToTable"] == to_table]

def parse_columns(file_path):
    columns = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
    for line in lines:
        parts = re.split(r'\s{2,}', line.strip())
        if len(parts) == 2 and parts[0] != "COLUMN_NAME":
            column, table = parts
            columns.append((column.lower(), table.lower()))
    return columns

def preprocess(text):
    return text.replace("_", " ")

def match_request_to_columns(user_request, columns, threshold=0.5):
    # Split user request into words
    # request_tokens = re.findall(r'\w+', user_request.lower())

    ranked_results = []
    # list_col = list(columns)

    sep_col = [tbl + " " + col for tbl, col in columns]
    # print(len(sep_col), len(list_col))

    # for token in request_tokens:
    corpus = [preprocess(user_request)] + [preprocess(col) for col in sep_col]
    vectorizer = TfidfVectorizer(stop_words='english').fit_transform(corpus)
    vectors = vectorizer.toarray()

    token_vec = vectors[0]
    col_vecs = vectors[1:]

    sims = cosine_similarity([token_vec], col_vecs)[0]

    # Rank columns by similarity and filter by threshold
    ranked_results = [(columns[i], sims[i]) for i in range(len(columns)) if sims[i] >= threshold]
    # ranked_results.append(results)
    # print(ranked_results, threshold)
    
    ranked_results = sorted(
    ranked_results,
    key=lambda res: res[0][1] if res else 0,
    reverse=True
)

    return ranked_results

def generate_query(user_request, columns, threshold=0.5):
    ranked = match_request_to_columns(user_request, columns, threshold)

    if not ranked:
        return "-- No columns matched above threshold"

    # Pick matches for SELECT
    select_cols = []
    tables_used = set()
    for (col, tbl), score in ranked:
        select_cols.append(f"{tbl}.{col}")
        tables_used.add(tbl)

    # Anchor table: pick the one with most matches
    anchor_table = max(tables_used, key=lambda t: sum(1 for (c, tb), _ in ranked if tb == t))

    # Build query skeleton
    select_clause = "SELECT " + ", ".join(select_cols)
    from_clause = f"FROM {anchor_table}"
    query = f"{select_clause}\n{from_clause}\n-- TODO: add JOINs based on foreign keys or shared columns\n-- TODO: add GROUP BY / ORDER BY as needed"
    return query

if __name__ == "__main__":
    file_path = "columns.txt"
    user_request = "Write a query in SQL to display the department which contributes the highest payroll in each region. Output: region_name, department_id, department_name, total_employees, total_department_salary."
    columns = parse_columns(file_path)
    sql_query = generate_query(user_request, columns)
    print(sql_query)
