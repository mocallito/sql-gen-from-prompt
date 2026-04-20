import random
import string
from collections import defaultdict
import context_extract
import parser
import search

class gen_alias():
    def __init__(self):
        self.aliases = {}
        self.available_letters = list(string.ascii_lowercase)
        random.shuffle(self.available_letters)
        self.tables = set()
    
    def set(self, table):
        if table not in self.aliases.keys():
            self.aliases[table] = self.available_letters.pop(
                random.randrange(len(self.available_letters))
            )
        return self.aliases[table]

    def get(self, table):
        if table in self.aliases.keys():
            return self.aliases[table]
        return self.set(table)
    
def generate_query(user_request, columns, foreign_key_path, threshold=0.5):
    '''
    1.use tfidf and cosine to get relevant columns from table.
    2.go through the relevant tables and add their alias and call dfs
    3.look for the best path among the dfs and take the root table as anchor
    4.choose the relevant tables for select
    5.rest of select in comments
    6.join the relevant table of the best path with help of reference keys
    7.rest of join in comments
    '''

    # TODO: move the following away and build a class
    fk_list = parser.read_foreign_keys(foreign_key_path)
    # parser.print_foreign_keys(fk_list)

    graph = search.build_graph(fk_list)
    # print("Graph representation:")
    # for table, neighbors in graph.items():
    #    print(f"{table} -> {neighbors}")

    # belongs to generate_query
    ranked = context_extract.match_request_to_columns(user_request, columns, threshold)

    if not ranked:
        return "-- No columns matched above threshold"

    # Assign random letters to tables
    tables = {tbl for (tbl, col), score in ranked}
    aliases = gen_alias()
    # for i, tbl in enumerate(tables):
    #     aliases[tbl] = available_letters[i]

    # Pick matches for SELECT
    select_cols = []
    all_cols = []
    # gets overwritten since it is a dict and not list
    for i, content in enumerate(ranked):
        (tbl, col), score = content
        alias = aliases.set(tbl)
        path = []
        search.dfs(graph, tbl, path)  # DFS for each table (piggy ride)
        path.remove(tbl)
        if isinstance(col, list):
            for c in col:
                select_cols.append(f"{alias}.{c}")
                all_cols.append((tbl, alias, path))
        else:
            select_cols.append(f"{alias}.{col}")
            all_cols.append((tbl, alias, path))

    # for item in all_cols:
    #     print(item)

    # Anchor table: pick the one with most join needed
    # Find the key with the longest list
    longest_path = max(all_cols, key=lambda col: len(col[2]))
    anchor_table, _, chosen_path = longest_path
    # print(anchor_table, chosen_path)
    anchor_alias = aliases.get(anchor_table)

    # FROM clause: anchor table with alias
    from_clause = f"FROM {anchor_table} {anchor_alias}"
    
    orphan_tables = []
    for el in all_cols:
        for col in select_cols:
            if (el[0] != anchor_table) and (el[0] not in chosen_path) and el[1]+"." in col:
                select_cols.remove(col)
                orphan_tables.append(col)
            # all_cols.pop(i)
    select_clause = "SELECT " + ",\n ".join(select_cols)
    select_clause = select_clause + "\n-- " + ",\n-- ".join(orphan_tables)

    # Build JOINs based on path of the anchor_table, do_while loop fashion
    joins = []
    prev_chosen_node = anchor_table
    for node in chosen_path:
        # print(node)
        fk = context_extract.find_relation(fk_list, prev_chosen_node, node)
        alias = aliases.get(prev_chosen_node)
        neigh_alias = aliases.get(node)
        if len(fk) > 0:
            joins.append(
                            f"JOIN {node} {neigh_alias} \n\t ON {alias}.{fk[0]['FromColumn']} = {neigh_alias}.{fk[0]['ToColumn']}"
                        )
        prev_chosen_node = node
    # The rest of the paths, find a better prev_table
    prev_table = prev_chosen_node
    for col in all_cols:
        # Check if chosen path has any miss
        table, alias, path = col
        if table in chosen_path:
            prev_node = None
            node_in_orphan_path = False
            for node in path: # if all node found skip the following somehow
                if node not in chosen_path:
                    node_in_orphan_path = True
                    break
                prev_node = node
            if node_in_orphan_path:
                for node in path:
                    neigh_alias = aliases.get(node)
                    prev_alias = aliases.get(prev_node)
                    fk = context_extract.find_relation(fk_list, prev_node, node)
                    if len(fk) > 0:
                        joins.append(
                                f"-- JOIN {node} {neigh_alias} \n\t ON {prev_alias}.{fk[0]['FromColumn']} = {neigh_alias}.{fk[0]['ToColumn']}"
                                    )
        else:
            # find connect from chosen to this
            fk = context_extract.find_relation(fk_list, prev_table, table)
            tabl_alias = aliases.get(table)
            prev_alias = aliases.get(prev_table)
            if len(fk) > 0:
                joins.append(
                                f"-- JOIN {table} {tabl_alias} \n\t ON {prev_alias}.{fk[0]['FromColumn']} = {tabl_alias}.{fk[0]['ToColumn']}"
                            )
            # continue path joining, could make a function of this
            prev_chosen_node = table
            for node in path:
                fk = context_extract.find_relation(fk_list, prev_chosen_node, node)
                alias = aliases.get(prev_chosen_node)
                neigh_alias = aliases.get(node)
                if len(fk) > 0:
                    joins.append(
                                    f"-- JOIN {node} {neigh_alias} \n\t-- ON {alias}.{fk[0]['FromColumn']} = {neigh_alias}.{fk[0]['ToColumn']}"
                                )
                prev_chosen_node = node
        prev_table = table
        
    # for col, tbls in all_cols.items():
    #     if len(tbls) > 1:
    #         for t, alias, path in tbls:
    #             if t != anchor_table:
    #                 joins.append(
    #                     f"JOIN {t} {alias} \n\t ON {anchor_alias}.{col} = {alias}.{col}"
    #                 )

    query = f"{select_clause}\n{from_clause}\n" + "\n".join(joins)
    print(aliases.aliases)
    return query

if __name__ == "__main__":
    overall_table_path = "all columns.txt"  # replace with your file path
    foreign_key_path = "foreign constraints.txt"
    user_request = "Write a query in SQL to display the department which contributes the highest payroll in each region. Output: region_name, department_id, department_name, total_employees, total_department_salary."
    #fk_list = parser.read_foreign_keys(foreign_key_path)
    # parser.print_foreign_keys(fk_list)

    #graph = search.build_graph(fk_list)

    #print("Graph representation:")
    #for table, neighbors in graph.items():
    #    print(f"{table} -> {neighbors}")

    # search.dfs(graph, "employees")  # start traversal from 'countries'

    columns = parser.parse_columns(overall_table_path)

    sql_query = generate_query(user_request.lower(), columns, foreign_key_path, threshold=0.2)
    print(sql_query)
