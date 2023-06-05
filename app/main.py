import json
from datetime import datetime
from timeit import default_timer as timer

import uvicorn
from connect_to_devices import (
    connection,
    delete_links,
    dev_creds,
    identify_blocked_links,
    identify_neighbor_device_in_a_blocked_link,
    identify_root_bridge,
    modify_node_levels,
    parse_cdp_lldp_output,
    parse_stp_output,
    process_edges,
    process_nodes,
    remove_duplicate_edges,
)
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from helper import static_nodes_edges

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root_endpoint():
    return {"message": "App is working", "time": datetime.now()}


@app.get("/graph/stp")
async def stp_endpoint():
    start = timer()

    filename = "./devices.json"
    devices = dev_creds(filename)

    conn_result, data_list = connection(devices)
    if conn_result.get("error"):
        # return {
        #     "elapsed_time": f"It took {round(timer() - start, 2)} s",
        #     "error": {"exception_msg": conn_result.get("exception_msg")},
        # }
        raise HTTPException(
            status_code=503,
            detail=conn_result.get("exception_msg"),
        )

    parsed_stp_list = parse_stp_output(data_list)
    parsed_cdp_lldp_list = parse_cdp_lldp_output(data_list)

    root_bridge_data = identify_root_bridge(data_list)

    data_list = modify_node_levels(root_bridge_data, data_list, parsed_cdp_lldp_list)
    nodes = process_nodes(data_list)

    edges = process_edges(nodes, parsed_cdp_lldp_list)
    print("\nAntes de remover edges", edges)

    edges = remove_duplicate_edges(edges)
    print("\nDespues de remover duplicated edges", edges)

    blocked_links = identify_blocked_links(parsed_stp_list, nodes, edges)
    print("\nblocked_links = ", blocked_links)

    links_to_be_deleted = identify_neighbor_device_in_a_blocked_link(
        blocked_links, parsed_cdp_lldp_list, nodes
    )
    print(f"\n{links_to_be_deleted = }")

    edges = delete_links(edges, links_to_be_deleted)

    return {
        "stp": parsed_stp_list,
        "cdp": parsed_cdp_lldp_list,
        "data_list": data_list,
        "nodes": nodes,
        "edges": edges,
    }

    # return {"nodes": nodes, "edges": edges}

    # nodes, edges = static_nodes_edges()
    # return {"nodes": nodes, "edges": edges}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=4)
