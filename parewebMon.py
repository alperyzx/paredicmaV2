# !/usr/bin/python
#paredicma webview v1.0
#date: 27.02.2024
#author: alperyz


import os
import sys

from pareConfig import *
from pareNodeList import *
from pareFunc import *
from pareFuncWeb import *

from fastapi import *
from fastapi.responses import HTMLResponse  # Import HTMLResponse
from subprocess import getstatusoutput

# Create an instance of FastAPI
app = FastAPI()
router = APIRouter()

# Define the ping-nodes endpoint
@app.get("/monitor/ping-nodes/")
def ping_nodes():
    pong_number = 0
    non_pong_number = 0
    ping_results = []

    for pareNode in pareNodes:
        node_ip = pareNode[0][0]
        port_number = pareNode[1][0]
        
        if pareNode[4]:
            isPing = pingredisNode(node_ip, port_number)
            if isPing:
                ping_result = [node_ip, port_number, "OK"]
                pong_number += 1
            else:
                ping_result = [node_ip, port_number, "NOT OK"]
                non_pong_number += 1
            ping_results.append(ping_result)

    # Prepare the table content with inline CSS styles
    table_content = "<table><tr><th>Server IP</th><th>Port</th><th>Status</th></tr>"
    for result in ping_results:
        if result[2] == "OK":
            status_style = "color: green;"
        else:
            status_style = "color: red;"
        table_content += f"<tr><td>{result[0]}</td><td>{result[1]}</td><td style='{status_style}'>{result[2]}</td></tr>"
    table_content += "</table>"

    # Prepare the response message
    response_message = f"{css_style}<html><title>Pinging Nodes</title><body><h2>Pinging Nodes...</h2>{table_content}<p>OK Nodes = {pong_number}<br>Not OK Nodes = {non_pong_number}</p></body></html>"

    # Return the response with content type set to text/html
    return Response(content=response_message, media_type="text/html")


# Define the list-nodes endpoint
@app.get("/monitor/list-nodes/")
def list_nodes():
    master_node_list = ''
    slave_node_list = ''
    unknown_node_list = ''
    down_node_list = ''
    node_number = 0

    for pare_node in pareNodes:
        node_ip = pare_node[0][0]
        port_number = pare_node[1][0]
        node_number += 1

        if pare_node[4]:
            if pingServer(node_ip):  # Check if the server is reachable
                if is_ssh_available(node_ip):  # Check if SSH connection is available
                    if pingredisNode(node_ip,port_number):  # Check if the Redis node is pingable
                        return_val = slaveORMasterNode(node_ip, port_number)
                        if return_val == 'M':
                            master_node_list += f'<b style="color: green;">Server IP :</b> <span style="color: green;">{node_ip}</span> <b style="color: green;">Port:</b> <span style="color: green;">{port_number}</span> <span style="color: green;">UP</span><br>'
                        elif return_val == 'S':
                            status, response = getstatusoutput(redisConnectCmd(node_ip, port_number, ' info replication | grep  -e "master_host:" -e "master_port:" '))
                            if status == 0:
                                response = response.replace("\nmaster_port", "")
                                slave_node_list += f'<b style="color: blue;">Server IP :</b> <span style="color: blue;">{node_ip}</span> <b style="color: blue;">Port:</b> <span style="color: blue;">{port_number}</span> <span style="color: blue;">UP</span> -> <span style="color: blue;">{response}</span><br>'
                            else:
                                slave_node_list += f'<b style="color: blue;">Server IP :</b> <span style="color: blue;">{node_ip}</span> <b style="color: blue;">Port:</b> <span style="color: blue;">{port_number}</span> <span style="color: red;">DOWN</span><br>'
                        else:
                            down_node_list += f'<b style="color: red;">Server IP :</b> <span style="color: red;">{node_ip}</span> <b style="color: red;">Port:</b> <span style="color: red;">{port_number}</span> <span style="color: red;">DOWN</span><br>'
                    else:
                        unknown_node_list += f'<b style="color: gray;">Server IP :</b> <span style="color: gray;">{node_ip}</span> <b style="color: gray;">Port:</b> <span style="color: gray;">{port_number}</span> <span style="color: red;">No Ping</span><br>'
                else:
                    unknown_node_list += f'<b style="color: gray;">Server IP :</b> <span style="color: gray;">{node_ip}</span> <b style="color: gray;">Port:</b> <span style="color: gray;">{port_number}</span> <span style="color: red;">No SSH connection</span><br>'
            else:
                unknown_node_list += f'<b style="color: gray;">Server IP :</b> <span style="color: gray;">{node_ip}</span> <b style="color: gray;">Port:</b> <span style="color: gray;">{port_number}</span> <span style="color: red;">Server Unreachable</span><br>'

    # Prepare the response message
    response_message = f"{css_style}<html><title>Node List</title><body><h2>Master Nodes</h2>{master_node_list}<h2>Slave Nodes</h2>{slave_node_list}<h2>Down Nodes</h2>{down_node_list}<h2>Unknown Nodes</h2>{unknown_node_list}</body></html>"

    # Return the response with content type set to text/html
    return Response(content=response_message, media_type="text/html")


# Define the node-info endpoint
@app.get("/monitor/node-info/")
def get_node_info(redisNode, command):

    # Call the nodeInfo function to retrieve information about the node
    node_info_val = nodeInfo_wv(redisNode, command)

    # Construct the response message in HTML format
    response_message = f"{css_style}<html><body><h2>Node Info</h2><p>RedisNode: {redisNode}<br>Command: {command}<br>{node_info_val}</p></body></html>"

    return Response(content=response_message, media_type="text/html")

@app.get("/monitor/server-info/")
async def get_server_info(server_ip: str):
        # Call the serverInfo function to retrieve server information
        server_info = serverInfo_wv(server_ip)
        
        # Construct the HTML response
        html_content = f"""
        {css_style}
        <!DOCTYPE html>
        <html>
        <title>Server Info</title>
        <head>
        </head>
        <body>
            <p>{server_info}</p>
        </body>
        </html>
        """
        return Response(content=html_content, media_type="text/html")


# Modify the monitor_slot_info endpoint to return HTML-formatted cluster information
@app.get("/monitor/slot-info/", response_class=Response)
async def monitor_slot_info():
    html_content = f"{css_style}<html><title>Cluster Slot Info</title><body>"
    for pareNode in pareNodes:
        nodeIP = pareNode[0][0]
        portNumber = pareNode[1][0]
        if pareNode[4] and validIP(nodeIP):
            isPing = pingredisNode(nodeIP, portNumber)
            if isPing:
                try:
                    cluster_info = slotInfo_wv(nodeIP, portNumber)
                    if cluster_info:
                        # Format the cluster information in HTML
                        html_content += f"<pre>{cluster_info}</pre>"
                        break  # Stop processing after getting information from one node
                except Exception as e:
                    print(f"Error retrieving cluster information for Node IP: {nodeIP}, Port: {portNumber}")
                    print(f"Error message: {str(e)}")
                    continue  # Continue to the next node

    if "<h2>" not in html_content:  # Check if no cluster information is found
        html_content += "<h2>No cluster information available</h2>"

    html_content += "</body></html>"
    return Response(content=html_content, media_type="text/html")


# Define the endpoint to retrieve cluster state information
@app.get("/monitor/cluster-state-info", response_class=HTMLResponse)
async def monitor_cluster_state_info():
    all_cluster_state_info = ""  # Initialize variable to hold information for all nodes
    for pareNode in pareNodes:
        nodeIP = pareNode[0][0]
        portNumber = pareNode[1][0]
        if pareNode[4]:
          isPing = pingredisNode(nodeIP, portNumber)
          try:
            if isPing:
                # Retrieve cluster state information for the node
                cluster_state_info = clusterStateInfo_wv(nodeIP, portNumber)
                # Determine the color based on the cluster state
                color = "green" if "ok" in cluster_state_info.lower() else "red"
                # Append the cluster state information to the overall information
                all_cluster_state_info += f"{css_style}<p style='color: {color};'>RedisNode: {nodeIP}:{portNumber} :: <b>{cluster_state_info}</b> </p>"
            else:
                # Node is unreachable, add it to the response with a label
                all_cluster_state_info += f"{css_style}<p style='color: gray;'>RedisNode: {nodeIP}:{portNumber} :: Unreachable</p>"
          except Exception as e:
            print(f"Error retrieving cluster information for RedisNode: {nodeIP}:{portNumber}")
            print(f"Error message: {str(e)}")
            continue  # Continue to the next node

    return all_cluster_state_info



@app.get("/monitor/memory-usage", response_class=HTMLResponse)
async def show_memory_usage():
    memory_usage_info = "<title>Memory Usage</title><h2>Memory Usage</h2>"
    memory_usage_info += "<table border='1'><tr><th>NodeType</th><th>NodeNum</th><th>NodeIP</th><th>NodePort</th><th>UsedMem(GB)</th><th>MaxMem(GB)</th><th>Usage(%)</th></tr>"
    total_used_mem_byte = 0
    total_max_mem_byte = 0
    master_nodes_info = ""
    slave_nodes_info = ""
    down_nodes_info = ""
    for node_number, pare_node in enumerate(pareNodes, start=1):
        if pare_node[4]:  # Check if the node is marked as active
            node_ip = pare_node[0][0]
            port_number = pare_node[1][0]

            # Check SSH availability first
            if is_ssh_available(node_ip):
                isPing = pingredisNode(node_ip, port_number)
                if isPing:
                    mem_status, mem_response = subprocess.getstatusoutput(
                        redisConnectCmd(node_ip, port_number, ' info memory | grep  -e "used_memory:" -e "maxmemory:" '))
                    if mem_status == 0:
                        used_mem_byte = float(mem_response[12:mem_response.find('maxmemory:') - 1])
                        max_mem_byte = float(mem_response[mem_response.find('maxmemory:') + 10:])
                        used_mem_gb = round(used_mem_byte / (1024 * 1024 * 1024), 3)
                        max_mem_gb = round(max_mem_byte / (1024 * 1024 * 1024), 3)
                        usage_per_mem = round((used_mem_gb / max_mem_gb) * 100, 2)
                        total_used_mem_byte += used_mem_byte
                        total_max_mem_byte += max_mem_byte
                        node_type = "Master" if isNodeMaster(node_ip, node_number, port_number) else "Slave"
                        usage_color = "#d3ffce" if usage_per_mem < 70 else "yellow" if 70 <= usage_per_mem < 85 else "red"
                        node_info = f"{css_style}<tr style='background-color:{usage_color};'><td>{node_type}</td><td>{node_number}</td><td>{node_ip}</td><td>{port_number}</td><td>{used_mem_gb}</td><td>{max_mem_gb}</td><td>{usage_per_mem}</td></tr>"
                        if node_type == "Master":
                            master_nodes_info += node_info
                        else:
                            slave_nodes_info += node_info
                    else:
                        print(
                            f"Error retrieving memory information for Node IP: {node_ip}, Port: {port_number}")
                else:
                    down_nodes_info += f"<tr><td>Down</td><td>{node_number}</td><td>{node_ip}</td><td>{port_number}</td><td></td><td></td><td></td></tr>"
            else:
                down_nodes_info += f"<tr><td>Unknown</td><td>{node_number}</td><td>{node_ip}</td><td>{port_number}</td><td></td><td></td><td></td></tr>"

    memory_usage_info += master_nodes_info + slave_nodes_info + down_nodes_info

    memory_usage_info += "</table>"

    total_used_mem = round((total_used_mem_byte / (1024 * 1024 * 1024)), 3)
    total_max_mem = round((total_max_mem_byte / (1024 * 1024 * 1024)), 3)
    total_mem_per = round(((total_used_mem / total_max_mem) * 100), 2)

    memory_usage_info += f"<p><b>Total (Only Master):</b> {total_used_mem}GB / {total_max_mem}GB ({total_mem_per}%)</p>"

    return HTMLResponse(content=memory_usage_info)



# Define the CSS style for the monitoring page
css_style = """
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            margin: 20px;
        }
        h1 {
            color: #333333;
        }
        th{
            text-align:left;
          }
        ul {
            list-style-type: none;
            padding: 0;
        }
        li {
            margin-bottom: 10px;
        }
        label {
            display: inline-block;
            width: 100px;
            margin-right: 10px;
        }
        input[type="text"], select {
            width: 160px;
            padding: 5px;
            border: 1px solid #cccccc;
            border-radius: 5px;
        }
        input[type="submit"], a {
            padding: 5px 10px;
            background-color: #007bff;
            color: #ffffff;
            text-decoration: none;
            border-radius: 5px;
        }
        input[type="submit"]:hover, a:hover {
            background-color: #0056b3;
        }
    </style>
"""

# Define the endpoint for the monitoring page
@app.get("/monitor", response_class=HTMLResponse)
async def monitor():
    uniqueservers = getuniqueServers(pareNodes)
    commandsAvailable = ['server', 'clients', 'memory', 'persistence', 'stats', 'replication', 'cpu', 'cluster']
    nodeList = getNodeList()
    # Generate the HTML content for the monitoring page
    html_content = f"""
    {css_style}
    <h1>Monitoring Endpoints</h1>
    <ul>
        <li><a href="/monitor/ping-nodes/">Ping Nodes</a></li>
        <li><a href="/monitor/list-nodes/">List Nodes</a></li>
        <li>
            <form action="/monitor/node-info/" method="get">
                <label for="redisNode">redisNode:</label>
                <select id="redisNode" name="redisNode">
                    {''.join([f"<option value='{node}'>{node}</option>" for node in nodeList])}
                </select>
                <select id="command" name="command">
                    {''.join([f"<option value='{command}'>{command}</option>" for command in commandsAvailable])}
                </select>
                <input type="submit" value="Submit">
            </form>
        </li>
        <li>
            <form action="/monitor/server-info/" method="get">
                <label for="server_id">Server Info:</label>
                <select id="server_id" name="server_ip">
                   {''.join([f"<option value='{server}'>{server}</option>" for server in uniqueservers])}
                </select>
                <input type="submit" value="Submit">
            </form>
        </li>
        <li><a href="/monitor/slot-info/">Slot Info</a></li>
        <li><a href="/monitor/cluster-state-info/">Cluster State Info</a></li>
        <li><a href="/monitor/memory-usage/">Memory Usage</a></li>
    </ul>
    <script>
        // Capture form submission and navigate to the corresponding endpoint
        document.querySelectorAll('form').forEach(form => {{
            form.addEventListener('submit', function(event) {{
                event.preventDefault(); // Prevent default form submission behavior
                const formData = new FormData(this); // Get form data
                const trimmedData = {{}}; // Object to hold trimmed data
                // Iterate over form data and trim input values
                for (const [key, value] of formData.entries()) {{
                    trimmedData[key] = value.trim(); // Trim whitespace from input values
                }}
                const url = this.getAttribute('action'); // Get form action URL
                const queryParams = new URLSearchParams(trimmedData).toString(); // Convert form data to query string
                const fullUrl = `${{url}}?${{queryParams}}`; // Combine URL with query string
                window.location.href = fullUrl; // Redirect to the new URL
            }});
        }});
    </script>
    """
    return HTMLResponse(content=html_content)



# #############################################

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=(pareWebPort))
