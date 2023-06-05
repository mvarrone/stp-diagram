def static_nodes_edges():
    nodes = [
        {"id": 0, "label": "SW 4", "level": 0, "title": "Huawei"},
        {
            "id": 1,
            "label": "SW CBA",
            "level": 1,
            "title": "192.168.238.129 - cisco_ios",
        },
        {"id": 2, "label": "2", "level": 3},
        {"id": 3, "label": "3", "level": 4},
        {"id": 4, "label": "4", "level": 4},
        {"id": 5, "label": "Switch AR-1", "level": 5},
        {"id": 6, "label": "6", "level": 1, "title": "Juniper"},
        {"id": 7, "label": "7", "level": 2},
        {"id": 8, "label": "8", "level": 4},
        {"id": 9, "label": "9", "level": 4},
        {"id": 10, "label": "10", "level": 2},
        {"id": 11, "label": "11", "level": 1},
        {"id": 12, "label": "12", "level": 2},
        {"id": 13, "label": "13", "level": 1},
        {"id": 14, "label": "14", "level": 5},
    ]

    edges = [
        {"from": 0, "to": 1},
        {"from": 0, "to": 6},
        {"from": 0, "to": 11},
        {"from": 0, "to": 13},
        {"from": 1, "to": 2},
        {"from": 2, "to": 3},
        {"from": 2, "to": 4},
        {"from": 3, "to": 5},
        {"from": 1, "to": 10},
        {"from": 1, "to": 7},
        {"from": 2, "to": 8},
        {"from": 2, "to": 9},
        {"from": 3, "to": 14},
        {"from": 1, "to": 12},
    ]

    return nodes, edges
