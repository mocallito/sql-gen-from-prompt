from collections import defaultdict

from collections import defaultdict, deque

def build_graph(fk_list):
    """
    Build a directed graph from the foreign key list.
    Returns adjacency list representation: {table: [related_tables]}.
    """
    graph = defaultdict(list)
    for fk in fk_list:
        from_table = fk["FromTable"]
        to_table = fk["ToTable"]
        graph[from_table].append(to_table)
    return graph

def traverse_tables(graph, start_table):
    """
    Traverse the graph starting from a given table using BFS.
    Returns the order of traversal.
    """
    visited = set()
    order = []
    queue = deque([start_table])

    while queue:
        table = queue.popleft()
        if table not in visited:
            visited.add(table)
            order.append(table)
            for neighbor in graph.get(table, []):
                if neighbor not in visited:
                    queue.append(neighbor)
    return order

def dfs(graph, start, visited=None):
    if visited is None:
        visited = []
    visited.append(start)
    # print(visited)
    # print(f"Visiting: {start}")
    for neighbor in graph[start]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited)
