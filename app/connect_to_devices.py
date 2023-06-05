import json

from netmiko import ConnectHandler
from ntc_templates.parse import parse_output


def get_prompt(conn):
    prompt = conn.find_prompt()
    # print(f"{prompt = }")
    if not prompt:
        return "prompt not found"

    if prompt[-1] == "#":
        prompt = prompt[:-1]

    print(f"{prompt = }")
    return prompt


def dev_creds(filename):
    with open(filename) as file:
        devices = json.load(file)
    return devices


def determine_root_bridge(prompt, device_type, stp_raw_output):
    is_root_bridge = False

    if device_type == "cisco_ios":
        if "This bridge is the root" in stp_raw_output:
            print(f"** {prompt} is the root bridge **")
            is_root_bridge = True
    return is_root_bridge


def connection(devices):
    data_list = []

    for count, device in enumerate(devices):
        print(f"\n{count = }")
        print(f"{device = }")
        try:
            device_type = device.get("device_type")
            device_credentials_only = {
                "device_type": device_type,
                "ip": device.get("ip"),
                "port": device.get("port"),
                "username": device.get("username"),
                "password": device.get("password"),
                "secret": device.get("secret"),
            }

            with ConnectHandler(**device_credentials_only) as conn:
                conn.enable()

                # Prompt
                prompt = get_prompt(conn)

                # STP
                stp_command = device.get("stp_command")
                stp_raw_output = conn.send_command(
                    stp_command, strip_prompt=False, strip_command=True
                )

                # Determine the root bridge
                is_root_bridge = determine_root_bridge(
                    prompt, device_type, stp_raw_output
                )

                # CDP or LLDP
                neighbors_command = device.get("neighbors_command")
                cdp_lldp_raw_output = conn.send_command(
                    neighbors_command, strip_prompt=False, strip_command=True
                )

                data = {
                    "count": count,
                    "prompt": prompt,
                    "stp_raw_output": stp_raw_output,
                    "cdp_lldp_raw_output": cdp_lldp_raw_output,
                    "stp_command": stp_command,
                    "neighbors_command": neighbors_command,
                    "device_type": device_type,
                    "is_root_bridge": is_root_bridge,
                    "level": 0 if is_root_bridge else 9999,
                    "ip_address": device.get("ip"),
                }
                data_list.append(data)
        except Exception as e:
            print("\n------------ EXCEPTION ------------", e)
            conn_result = {"error": True, "exception_msg": str(e)}
            return conn_result, data_list

    conn_result = {"error": False}
    return conn_result, data_list


def correct_stp_parsed_data(device_type, parsed_output):
    if device_type == "cisco_ios":
        for output in parsed_output:
            intf_name = output.get("interface")
            intf_type = output.get("type")
            intf_role = output.get("role")
            intf_status = output.get("status")

            if intf_name.startswith("Et"):  # Standarization
                output["interface"] = f"e{intf_name[2:]}"

            if intf_type == "P2p ":  # Deleting a trailing space
                output["type"] = "P2p"

            # Roles
            if intf_role == "Altn":  # Standarization
                output["role"] = "alternate"

            if intf_role == "Root":  # Standarization
                output["role"] = "root"

            if intf_role == "Desg":  # Standarization
                output["role"] = "designated"

            # Status
            if intf_status == "BLK":  # Standarization
                output["status"] = "blocking"

            if intf_status == "FWD":  # Standarization
                output["status"] = "forwarding"

            if intf_status == "LIS":  # Standarization
                output["status"] = "listening"

            if intf_status == "LRN":  # Standarization
                output["status"] = "learning"

    return parsed_output


def parse_stp_output(data_list):
    parsed_stp_list = []

    # Parse raw STP
    for data in data_list:
        device_type = data.get("device_type")
        stp_command = data.get("stp_command")
        stp_raw_output = data.get("stp_raw_output")
        prompt = data.get("prompt")

        parsed_output = parse_output(
            platform=device_type, command=stp_command, data=stp_raw_output
        )

        parsed_output = correct_stp_parsed_data(device_type, parsed_output)

        out_stp = {prompt: parsed_output}
        parsed_stp_list.append(out_stp)

    return parsed_stp_list


def correct_cdp_parsed_data(device_type, parsed_output, prompt):
    if device_type == "cisco_ios":
        for index, output in enumerate(parsed_output):
            neighbor = output.get("neighbor")
            local_interface = output.get("local_interface")
            neighbor_interface = output.get("neighbor_interface")
            platform = output.get("platform")

            if neighbor == f"{prompt}#":
                del parsed_output[index]

            if len(neighbor.split(".")) > 1:
                output["neighbor"] = neighbor.split(".")[0]

            if local_interface.startswith("Eth "):  # Standarization
                output["local_interface"] = f"e{local_interface[4:]}"

            if neighbor_interface.startswith("Uni Eth "):  # Standarization
                output["neighbor_interface"] = f"e{neighbor_interface[8:]}"
                output["platform"] = f"{platform} Uni"

    return parsed_output


def parse_cdp_lldp_output(data_list):
    parsed_cdp_lldp_list = []

    # Parse raw CDP/LLDP
    for data in data_list:
        device_type = data.get("device_type")
        neighbors_command = data.get("neighbors_command")
        cdp_lldp_raw_output = data.get("cdp_lldp_raw_output")
        prompt = data.get("prompt")

        parsed_output = parse_output(
            platform=device_type, command=neighbors_command, data=cdp_lldp_raw_output
        )

        parsed_output = correct_cdp_parsed_data(device_type, parsed_output, prompt)

        out_cdp_lldp = {prompt: parsed_output}
        parsed_cdp_lldp_list.append(out_cdp_lldp)

    return parsed_cdp_lldp_list


def identify_root_bridge(data_list):
    print(f"\n{data_list = }")

    root_bridge_data = {}
    for data in data_list:
        if data.get("is_root_bridge"):
            root_bridge_data = {
                "id": data.get("count"),
                "prompt": data.get("prompt"),
                "device_type": data.get("device_type"),
                "level": data.get("level"),
            }
    return root_bridge_data


def modify_node_levels(root_bridge_data, data_list, parsed_cdp_lldp_list):
    root_bridge_prompt = root_bridge_data.get("prompt")

    for parsed in parsed_cdp_lldp_list:
        if parsed.get(root_bridge_prompt):
            root_bridge_neighbors = parsed.get(root_bridge_prompt)

    print(f"\n\n{root_bridge_neighbors = }")

    for root_bridge_neighbor in root_bridge_neighbors:
        root_bridge_neighbor_prompt = root_bridge_neighbor.get("neighbor")
        print(f"\n{root_bridge_neighbor_prompt = }")

        for data in data_list:
            bridge_prompt = data.get("prompt")
            if bridge_prompt == root_bridge_neighbor_prompt:
                data.update({"level": 1})

    return data_list


def process_nodes(data_list):
    nodes = []
    for device in data_list:
        node = {
            "id": device.get("count"),
            "label": device.get("prompt"),
            "level": device.get("level"),
            "title": f"{ device.get('ip_address') } - { device.get('device_type') }",
        }
        nodes.append(node)
    return nodes


def process_edges(nodes, parsed_cdp_lldp_list):
    device_prompts = [node.get("label") for node in nodes]
    print(f"\n{device_prompts = }")

    print("\n------------ Empieza el calculo de EDGES ------------")
    edges = []
    for node in nodes:
        label_node = node.get("label")
        from_node = node.get("id")
        print(f"\n-----Switch: {label_node = }")
        print(f"id: {from_node = }")

        for idx, value in enumerate(parsed_cdp_lldp_list):
            print(f"\n{idx = }")
            print(f"{value = }")

            neighbors = value.get(label_node)
            if neighbors is not None:
                print(f"\nVecinos de {label_node} --> {neighbors = }")
                for neighbor in neighbors:
                    neighbor_label = neighbor.get("neighbor")
                    print(f"\n{neighbor_label = }")
                    for node in nodes:
                        # print(f"\n{node = }")
                        if node.get("label") == neighbor_label:
                            to_node = node.get("id")
                            print(f"{to_node = }")

                    edge = {"from": from_node, "to": to_node}
                    edges.append(edge)
    return edges


def fix_opposite_values(dictionary):
    if dictionary["from"] > dictionary["to"]:
        dictionary["from"], dictionary["to"] = dictionary["to"], dictionary["from"]
    return dictionary


def remove_duplicate_edges(dictionaries):
    processed_dicts = []
    seen = set()
    for dictionary in dictionaries:
        processed_dict = fix_opposite_values(dictionary)
        dict_tuple = tuple(sorted(processed_dict.items()))
        if dict_tuple not in seen:
            processed_dicts.append(processed_dict)
            seen.add(dict_tuple)
    return processed_dicts


def identify_blocked_links(parsed_stp_list, nodes, edges):
    print("\nIdentificando enlaces bloqueados")
    blocked_links = []
    for node in nodes:
        label_node = node.get("label")
        id_node = node.get("id")
        # print(f"\n{label_node = }")
        # print(f"\n{id_node = }")
        for switch in parsed_stp_list:
            if switch.get(label_node) is not None:
                info = switch.get(label_node)
                # print(f"{info = }")
                for intf in info:
                    if intf.get("role") == "alternate":
                        print(f"\n{label_node = }")
                        print(f"{id_node = }")
                        # print(f"{intf = }")
                        interface = intf.get("interface")
                        print(f"{interface = }")
                        blocked_link = {
                            "label_node": label_node,
                            "id_node": id_node,
                            "interface_blocked": interface,
                        }
                        blocked_links.append(blocked_link)
    return blocked_links


def identify_neighbor_device_in_a_blocked_link(
    blocked_links, parsed_cdp_lldp_list, nodes
):
    print("\n--------------- Identifying neighbor in a blocked link ---------------")
    links_to_be_deleted = []
    for link in blocked_links:
        print(f"\n{link = }")
        sw_name = link.get("label_node")
        sw_id = link.get("id_node")
        interface_blocked = link.get("interface_blocked")
        print(f"\n{sw_name = }")
        print(f"\n{interface_blocked = }")
        for parsed in parsed_cdp_lldp_list:
            print(f"\n{parsed = }")
            parsed_sw = parsed.get(sw_name)
            if parsed_sw is not None:
                print(f"\n{parsed_sw = }")
                for data in parsed_sw:
                    print("\n---data", data)
                    if interface_blocked == data.get("local_interface"):
                        neighbor_name = data.get("neighbor")
                        print(f"{neighbor_name = }")
                        for node in nodes:
                            if node.get("label") == neighbor_name:
                                neighbor_id = node.get("id")
                                print(f"{neighbor_id = }")
                                link = {"id_A": sw_id, "id_B": neighbor_id}
                                links_to_be_deleted.append(link)
    return links_to_be_deleted


def delete_links(edges, links_to_be_deleted):
    print("\ndelete_links(...) Direction: orderly")
    for idx, edge in enumerate(edges):
        print(f"\n{idx = }")
        print(f"{edge = }")
        for link in links_to_be_deleted:
            print(link)
            if edge.get("from") == link.get("id_A"):
                if edge.get("to") == link.get("id_B"):
                    print("ORDERLY: This is a match!")
                    del edges[idx]

    print("\ndelete_links(...) Direction: upside down")
    for link in links_to_be_deleted:
        print(f"\nBEFORE: {link = }")
        link["id_B"], link["id_A"] = link.get("id_A"), link.get("id_B")
        print(f"AFTER: {link = }")

        for idx, edge in enumerate(edges):
            print(f"{edge = }")
            if edge.get("from") == link.get("id_A"):
                if edge.get("to") == link.get("id_B"):
                    print("UPSIDE DOWN: This is a match!")
                    del edges[idx]

    print("\nFinal edges: ", edges)
    return edges
