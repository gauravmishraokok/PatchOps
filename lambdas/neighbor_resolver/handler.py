def handler(event, context):
    patched_file = event.get("patched_file")
    graph = event.get("graph", {"nodes": [], "edges": []})
    
    neighbors = set()
    for edge in graph.get("edges", []):
        if edge["source"] == patched_file:
            neighbors.add(edge["target"])
        if edge["target"] == patched_file:
            neighbors.add(edge["source"])
            
    all_nodes = {n["id"] for n in graph.get("nodes", [])}
    excluded = list(all_nodes - neighbors - {patched_file})
    neighbors = list(neighbors)
    
    reasoning = f"{patched_file} directly connects to: {', '.join(neighbors)}. " \
                f"{len(excluded)} files have no direct edge and are excluded."
                
    return {
        "neighbors": neighbors,
        "excluded": excluded,
        "reasoning": reasoning
    }
