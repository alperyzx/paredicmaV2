# !/usr/bin/python
#paredicma webview v1.0
#date: 27.02.2024
#author: alperyz


import os
import sys  # Ensure sys is imported for module reloading

from pareConfig import *
from pareNodeList import *
from pareFunc import *
from pareFuncWeb import *

from fastapi import *
from fastapi.responses import HTMLResponse  # Import HTMLResponse
from subprocess import getstatusoutput
from time import sleep  # Import sleep

# Create an instance of FastAPI
app = FastAPI()
router = APIRouter()

@app.middleware("http")
async def reload_nodes_middleware(request, call_next):
    """
    Middleware that reloads the pareNodes configuration before processing certain paths.
    This ensures the UI always shows the latest node configuration.
    """
    # List of paths that should trigger a configuration reload
    reload_paths = [
        "/monitor",  # Added main monitor page
        "/monitor/list-nodes/",
        "/monitor/ping-nodes/",
        "/monitor/node-info/",  # Added node-info endpoint
        "/monitor/slot-info/",
        "/monitor/cluster-state-info",
        "/monitor/memory-usage",
        "/maintain",
        "/manager"
    ]

    # Check if the current path should trigger a reload
    if any(request.url.path.startswith(path) for path in reload_paths):
        try:
            # Reload the pareNodeList module
            import importlib
            importlib.reload(sys.modules['pareNodeList'])
            from pareNodeList import pareNodes as fresh_pareNodes

            # Update the global pareNodes with the freshly loaded version
            global pareNodes
            pareNodes = fresh_pareNodes
        except Exception as e:
            print(f"Error reloading node configuration: {str(e)}")

    # Continue processing the request
    response = await call_next(request)
    return response

# Add an endpoint to manually refresh the node configuration
@app.get("/refresh-config", response_class=HTMLResponse)
async def refresh_config():
    """
    Endpoint to manually refresh the node configuration.
    """
    try:
        # Reload the pareNodeList module
        import importlib
        importlib.reload(sys.modules['pareNodeList'])
        from pareNodeList import pareNodes as fresh_pareNodes

        # Update the global pareNodes
        global pareNodes
        pareNodes = fresh_pareNodes

        # Generate the response message
        response_message = f"""
        {css_style}
        <html>
        <head><title>Configuration Refreshed</title></head>
        <body>
            <h2>Node Configuration Refreshed</h2>
            <p>The node configuration has been successfully reloaded.</p>
            <p>Current active nodes: {sum(1 for node in pareNodes if node[4])}</p>
            <div class="nav-buttons">
                <a href="/monitor">Back to Monitor</a>
                <a href="/maintain">Back to Maintenance</a>
                <a href="/manager">Back to Manager</a>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=response_message)
    except Exception as e:
        response_message = f"""
        {css_style}
        <html>
        <head><title>Configuration Refresh Failed</title></head>
        <body>
            <h2>Node Configuration Refresh Failed</h2>
            <p style='color: red;'>Error: {str(e)}</p>
            <div class="nav-buttons">
                <a href="/monitor">Back to Monitor</a>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=response_message)

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
    # Ensure we have the latest node list before processing the request
    try:
        import importlib
        importlib.reload(sys.modules['pareNodeList'])
        from pareNodeList import pareNodes as fresh_pareNodes
        global pareNodes
        pareNodes = fresh_pareNodes

        # Also refresh the nodeList
        nodeList = getNodeList()

        # Provide a message if the requested node isn't in the list
        if redisNode not in nodeList:
            return Response(
                content=f"{css_style}<html><body><h2>Node Not Found</h2>" +
                f"<p style='color: red;'>The node {redisNode} was not found in the current node list.</p>" +
                f"<p>This could happen if you're trying to access a newly added node. Please try refreshing the page or use the Refresh Configuration button.</p>" +
                f"<p><a href='/refresh-config' class='btn' style='background-color: #28a745; color: white;'>Refresh Configuration</a></p>" +
                "</body></html>",
                media_type="text/html"
            )
    except Exception as e:
        print(f"Error refreshing node list in node-info endpoint: {str(e)}")

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
        input[type="submit"] {
            padding: 5px 10px;
            background-color: #007bff;
            color: #ffffff;
            text-decoration: none;
            border-radius: 5px;
        }
        input[type="submit"]:hover {
            background-color: #0056b3;
        }
        a {
            padding: 5px 10px;
            background-color: #007bff;
            color: #ffffff;
            text-decoration: none;
            border-radius: 5px;
            display: inline-block;
            margin-right: 10px;
            margin-bottom: 5px;
        }
        a:hover {
            background-color: #0056b3;
        }
        .nav-buttons {
            margin-top: 15px;
        }
        .confirm-btn {
            background-color: #d9534f;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }
        .cancel-btn {
            background-color: #5bc0de;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            text-decoration: none;
        }
        .confirmation-needed {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 4px;
            padding: 20px;
            margin: 20px 0;
        }
        .config-table {
            border-collapse: collapse;
            width: 100%;
            margin-top: 20px;
        }
        .config-table th, .config-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        .config-table th {
            background-color: #f2f2f2;
        }
        .config-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        /* Welcome page specific styles */
        .welcome-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .welcome-header {
            text-align: center;
            margin-bottom: 30px;
        }
        .welcome-header h1 {
            font-size: 36px;
            color: #2c3e50;
        }
        .welcome-description {
            text-align: center;
            margin-bottom: 40px;
            color: #555;
            font-size: 18px;
        }
        .section-cards {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 20px;
        }
        .section-card {
            flex: 1;
            min-width: 250px;
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .section-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        .card-header {
            font-size: 24px;
            color: #2c3e50;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        .card-content {
            color: #555;
            margin-bottom: 20px;
            line-height: 1.5;
            min-height: 100px;
        }
        .card-footer {
            display: flex;
            justify-content: center;
        }
        .card-button {
            padding: 10px 15px;
            background-color: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            text-align: center;
            transition: background-color 0.3s;
            width: 100%;
        }
        .card-button:hover {
            background-color: #2980b9;
        }
        .monitor-card .card-header {
            color: #3498db;
        }
        .manager-card .card-header {
            color: #2ecc71;
        }
        .maintain-card .card-header {
            color: #e74c3c;
        }
        .monitor-card .card-button {
            background-color: #3498db;
        }
        .manager-card .card-button {
            background-color: #2ecc71;
        }
        .maintain-card .card-button {
            background-color: #e74c3c;
        }
        .monitor-card .card-button:hover {
            background-color: #2980b9;
        }
        .manager-card .card-button:hover {
            background-color: #27ae60;
        }
        .maintain-card .card-button:hover {
            background-color: #c0392b;
        }
    </style>
"""

# Add a root route handler for the welcome page
@app.get("/", response_class=HTMLResponse)
async def welcome_page():
    """
    Welcome page that serves as a landing page with links to the three main sections:
    Monitor, Manager, and Maintenance.
    """
    html_content = f"""
    {css_style}
    <!DOCTYPE html>
    <html>
    <head>
        <title>Paredicma - Redis Cluster Management</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <div class="welcome-container">
            <div class="welcome-header">
                <h1>Paredicma</h1>
                <div class="welcome-description">
                    Redis Cluster Management Tool
                </div>
            </div>
            
            <div class="section-cards">
                <div class="section-card monitor-card">
                    <h2 class="card-header">Monitor</h2>
                    <div class="card-content">
                        <p>View real-time status of your Redis cluster. Monitor node health, memory usage, and cluster state.</p>
                        <p>Key features include ping nodes, list nodes, check cluster slots, view memory usage and more.</p>
                    </div>
                    <div class="card-footer">
                        <a href="/monitor" class="card-button">Go to Monitor</a>
                    </div>
                </div>
                
                <div class="section-card manager-card">
                    <h2 class="card-header">Manager</h2>
                    <div class="card-content">
                        <p>Manage your Redis cluster operations such as start/stop/restart nodes, switch master/slave roles, and change configurations.</p>
                        <p>Execute commands across all nodes, perform rolling restarts, and view Redis logs.</p>
                    </div>
                    <div class="card-footer">
                        <a href="/manager" class="card-button">Go to Manager</a>
                    </div>
                </div>
                
                <div class="section-card maintain-card">
                    <h2 class="card-header">Maintenance</h2>
                    <div class="card-content">
                        <p>Perform maintenance tasks such as adding new nodes, deleting nodes, moving slots, and upgrading Redis versions.</p>
                        <p>Manage cluster topology, migrate data, and balance slot distribution.</p>
                    </div>
                    <div class="card-footer">
                        <a href="/maintain" class="card-button">Go to Maintenance</a>
                    </div>
                </div>
            </div>
            
            <div class="welcome-footer" style="margin-top: 40px; text-align: center; color: #777;">
                <p>Select a section above to start working with your Redis cluster</p>
                <p style="font-size: 12px;">Paredicma v1.0 - Redis Cluster Management Tool</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Define the endpoint for the monitoring page
@app.get("/monitor", response_class=HTMLResponse)
async def monitor():
    # Ensure we have the latest node list before displaying the page
    try:
        import importlib
        importlib.reload(sys.modules['pareNodeList'])
        from pareNodeList import pareNodes as fresh_pareNodes
        global pareNodes
        pareNodes = fresh_pareNodes
    except Exception as e:
        print(f"Error refreshing node list: {str(e)}")

    uniqueservers = getuniqueServers(pareNodes)
    commandsAvailable = ['server', 'clients', 'memory', 'persistence', 'stats', 'replication', 'cpu', 'cluster']
    nodeList = getNodeList()
    # Generate the HTML content for the monitoring page
    html_content = f"""
    {css_style}
    <h1>Monitoring Endpoints</h1>
    <div style="margin-bottom: 20px;">
        <a href="/manager">Go to Manager (paredicman)</a>
        <a href="/maintain">Go to Maintenance (paredicmaint)</a>
    </div>
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
# Manager Section
# #############################################

@app.get("/manager/node-action/", response_class=HTMLResponse)
async def node_action(redisNode: str, action: str, confirmed: bool = False):
    """
    Endpoint to start, stop, or restart a Redis node.
    Includes confirmation handling for stopping master nodes.
    """
    result_html = node_action_wv(redisNode, action, confirmed)

    # Check if this is a confirmation request (when result contains confirmation-needed)
    if "confirmation-needed" in result_html:
        # Return a simplified response with just the confirmation dialog
        response_message = f"""
        {css_style}
        <html>
        <head>
            <title>Confirm {action.capitalize()} Node {redisNode}</title>
        </head>
        <body>
            <h2>Node Action Confirmation Required</h2>
            {result_html}
        </body>
        </html>
        """
    else:
        # Construct the standard response message
        response_message = f"""
        {css_style}
        <html>
        <head><title>Node Action: {action} {redisNode}</title></head>
        <body>
            <h2>Node Action Result</h2>
            <p><b>Node:</b> {redisNode}<br><b>Action:</b> {action}</p>
            <div>{result_html}</div>
            <div class="nav-buttons">
                <a href="/manager">Back to Manager</a>
                <a href="/monitor">Back to Monitor</a>
            </div>
        </body>
        </html>
        """
    return HTMLResponse(content=response_message)

@app.get("/manager/switch-master-slave/", response_class=HTMLResponse)
async def switch_master_slave(redisNode: str):
    """
    Endpoint to switch roles between a master node and one of its slaves.
    """
    result_html = switch_master_slave_wv(redisNode)

    # Construct the response message
    response_message = f"""
    {css_style}
    <html>
    <head>
        <title>Switch Master/Slave Nodes</title>
        <style>
            .node-info {{
                background-color: #f8f9fa;
                padding: 10px;
                margin: 10px 0;
                border-radius: 4px;
                border-left: 4px solid #007bff;
            }}
        </style>
    </head>
    <body>
        <h2>Master/Slave Switch Result</h2>
        <p><b>Selected Node:</b> {redisNode}</p>
        <div>{result_html}</div>
        <div class="nav-buttons">
            <a href="/manager">Back to Manager</a>
            <a href="/monitor">Back to Monitor</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=response_message)

@app.get("/manager/change-config/", response_class=HTMLResponse)
async def change_config(redisNode: str, parameter: str, value: str, persist: bool = False):
    """
    Endpoint to change a Redis configuration parameter.
    """
    result_html = change_config_wv(redisNode, parameter, value, persist)

    # Construct the response message
    response_message = f"""
    {css_style}
    <html>
    <head><title>Change Redis Configuration</title></head>
    <body>
        <h2>Change Redis Configuration Result</h2>
        <p><b>Node:</b> {redisNode}<br><b>Parameter:</b> {parameter}<br><b>Value:</b> {value}</p>
        <div>{result_html}</div>
        <div class="nav-buttons">
            <a href="/manager/get-config/?redisNode={redisNode}">View Configuration</a>
            <a href="/manager">Back to Manager</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=response_message)

@app.get("/manager/get-config/", response_class=HTMLResponse)
async def get_config(redisNode: str, parameter: str = "*"):
    """
    Endpoint to get Redis configuration parameters.
    """
    result_html = get_config_wv(redisNode, parameter)

    # Construct the response message
    response_message = f"""
    {css_style}
    <html>
    <head><title>Redis Configuration</title></head>
    <body>
        <h2>Redis Configuration</h2>
        <p><b>Node:</b> {redisNode}</p>
        <div>{result_html}</div>
        <div class="nav-buttons">
            <a href="/manager">Back to Manager</a>
            <a href="/monitor">Back to Monitor</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=response_message)

@app.get("/manager/save-config/", response_class=HTMLResponse)
async def save_config(redisNode: str):
    """
    Endpoint to save Redis configuration to redis.conf file.
    Can be a specific node (IP:PORT) or "all" for all nodes.
    """
    result_html = save_config_wv(redisNode)

    # Construct the response message
    response_message = f"""
    {css_style}
    <html>
    <head><title>Save Redis Configuration</title></head>
    <body>
        <h2>Save Redis Configuration Result</h2>
        <p><b>Target:</b> {redisNode}</p>
        <div>{result_html}</div>
        <div class="nav-buttons">
            <a href="/manager">Back to Manager</a>
            <a href="/monitor">Back to Monitor</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=response_message)

@app.get("/manager/rolling-restart/", response_class=HTMLResponse)
async def rolling_restart(wait_minutes: int = 0, restart_masters: bool = True, confirmed: bool = False):
    """
    Endpoint to perform a rolling restart of Redis Cluster nodes.
    """
    if not confirmed:
        # Return a confirmation page
        return HTMLResponse(content=f"""
        {css_style}
        <html>
        <head>
            <title>Confirm Rolling Restart</title>
        </head>
        <body>
            <h2>Rolling Restart Confirmation</h2>
            <div class="confirmation-needed">
                <p style='color: orange; font-weight: bold;'>Warning: You are about to perform a rolling restart of the Redis Cluster!</p>
                <p>This will restart all nodes in the cluster with the following settings:</p>
                <ul>
                    <li><strong>Wait time between restarts:</strong> {wait_minutes} minute(s)</li>
                    <li><strong>Restart master nodes:</strong> {'Yes' if restart_masters else 'No (only slaves)'}</li>
                </ul>
                <p>Do you want to continue?</p>
                <form id="confirm-action-form" action="/manager/rolling-restart/" method="get">
                    <input type="hidden" name="wait_minutes" value="{wait_minutes}">
                    <input type="hidden" name="restart_masters" value="{str(restart_masters).lower()}">
                    <input type="hidden" name="confirmed" value="true">
                    <button type="submit" class="confirm-btn">Yes, Perform Rolling Restart</button>
                    <a href="/manager" class="cancel-btn">Cancel</a>
                </form>
            </div>
        </body>
        </html>
        """)

    # If confirmed, perform the rolling restart
    result_html = rolling_restart_wv(wait_minutes, restart_masters)

    # Construct the response message
    response_message = f"""
    {css_style}
    <html>
    <head><title>Rolling Restart</title></head>
    <body>
        <h2>Rolling Restart Results</h2>
        <div>{result_html}</div>
        <div class="nav-buttons">
            <a href="/manager">Back to Manager</a>
            <a href="/monitor">Back to Monitor</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=response_message)

@app.get("/manager/execute-command/", response_class=HTMLResponse)
async def execute_command(command: str, only_masters: bool = False, wait_seconds: int = 0):
    """
    Endpoint to execute a Redis command on all nodes or only on master nodes.
    """
    result_html = execute_command_wv(command, only_masters, wait_seconds)

    # Construct the response message
    response_message = f"""
    {css_style}
    <html>
    <head><title>Execute Redis Command</title></head>
    <body>
        <h2>Redis Command Execution Results</h2>
        <p><b>Command:</b> {command}<br>
        <b>Only Masters:</b> {'Yes' if only_masters else 'No'}<br>
        <b>Wait Between Nodes:</b> {wait_seconds} seconds</p>
        <div>{result_html}</div>
        <div class="nav-buttons">
            <a href="/manager">Back to Manager</a>
            <a href="/monitor">Back to Monitor</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=response_message)

@app.get("/manager/show-log/", response_class=HTMLResponse)
async def show_log(redisNode: str, line_count: int = 100):
    """
    Endpoint to display Redis log file content.
    """
    result_html = show_redis_log_wv(redisNode, line_count)

    # Construct the response message
    response_message = f"""
    {css_style}
    <html>
    <head>
        <title>Redis Log File</title>
        <style>
            pre {{
                white-space: pre-wrap;       /* Since CSS 2.1 */
                white-space: -moz-pre-wrap;  /* Mozilla, since 1999 */
                white-space: -pre-wrap;      /* Opera 4-6 */
                white-space: -o-pre-wrap;    /* Opera 7 */
                word-wrap: break-word;       /* Internet Explorer 5.5+ */
                overflow-x: auto;
            }}
        </style>
    </head>
    <body>
        <h2>Redis Log File</h2>
        <p><b>Node:</b> {redisNode}</p>
        <div>{result_html}</div>
        <div class="nav-buttons">
            <form id="refresh-form" action="/manager/show-log/" method="get">
                <input type="hidden" name="redisNode" value="{redisNode}">
                <input type="hidden" name="line_count" value="{line_count}">
                <input type="submit" value="Refresh Log">
            </form>
            <a href="/manager">Back to Manager</a>
            <a href="/monitor">Back to Monitor</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=response_message)

@app.get("/manager", response_class=HTMLResponse)
async def manager():
    """
    Displays the Redis Cluster Manager UI.
    """
    # Reload the pareNodes configuration to ensure the latest node list
    import importlib
    importlib.reload(sys.modules['pareNodeList'])
    from pareNodeList import pareNodes as fresh_pareNodes

    # Update the global pareNodes
    global pareNodes
    pareNodes = fresh_pareNodes

    nodeList = getNodeList()

    # Get only master nodes for the switch master/slave feature
    masterNodes = []
    for pareNode in pareNodes:
        nodeIP = pareNode[0][0]
        portNumber = pareNode[1][0]
        if pareNode[4]:  # If node is active
            if slaveORMasterNode(nodeIP, portNumber) == 'M':  # If node is a master
                masterNodes.append(f"{nodeIP}:{portNumber}")

    actionsAvailable = ['Start', 'Stop', 'Restart']

    # Common Redis configuration parameters for quick selection
    common_configs = [
        "maxmemory",
        "maxmemory-policy",
        "timeout",
        "maxclients",
        "requirepass",
        "appendonly",
        "appendfsync",
        "cluster-node-timeout",
        "slowlog-log-slower-than",
        "slowlog-max-len"
    ]

    # Generate the HTML content for the manager page
    html_content = f"""
    {css_style}
    <html>
    <head><title>Redis Cluster Manager</title></head>
    <body>
    <h1>Redis Cluster Manager (paredicman)</h1>
    <div class="nav-buttons">
        <a href="/monitor">Go to Monitor (paredicmon)</a>
        <a href="/maintain">Go to Maintenance (paredicmaint)</a>
    </div>
    <hr>

    <h2>1 - Start/Stop/Restart Redis Node</h2>
    <form id="node-action-form" action="/manager/node-action/" method="get">
        <label for="redisNodeAction">Select Node:</label>
        <select id="redisNodeAction" name="redisNode">
            {''.join([f"<option value='{node}'>{node}</option>" for node in nodeList])}
        </select>
        <br><br>
        <label for="action">Select Action:</label>
        <select id="action" name="action">
            {''.join([f"<option value='{action.lower()}'>{action}</option>" for action in actionsAvailable])}
        </select>
        <br><br>
        <input type="submit" value="Perform Action">
    </form>
    <hr>

    <h2>2 - Switch Master/Slave Nodes</h2>
            <form id="switch-master-slave-form" action="/manager/switch-master-slave/" method="get">
        <label for="masterNode">Select Master Node:</label>
        <select id="masterNode" name="redisNode">
            {''.join([f"<option value='{node}'>{node}</option>" for node in masterNodes])}
        </select>
        <br><br>
        <input type="submit" value="Switch Master/Slave">
    </form>
    <p><i>This will promote one of the master's</p>
    
    <hr>

    <h2>3 - Change Redis Configuration Parameter</h2>
    <form id="change-config-form" action="/manager/change-config/" method="get">
        <label for="configNode">Select Node:</label>
        <select id="configNode" name="redisNode">
            {''.join([f"<option value='{node}'>{node}</option>" for node in nodeList])}
        </select>
        <br><br>
        <label for="parameter">Parameter:</label>
        <select id="parameter" name="parameter">
            <option value="">--- Select or type below ---</option>
            {''.join([f"<option value='{param}'>{param}</option>" for param in common_configs])}
        </select>
        <br><br>
        <label for="custom-parameter">Or type parameter:</label>
        <input type="text" id="custom-parameter" placeholder="e.g., maxmemory">
        <br><br>
        <label for="value">New Value:</label>
        <input type="text" id="value" name="value" placeholder="e.g., 2gb">
        <br><br>
        <label for="persist">Persist to config:</label>
        <input type="checkbox" id="persist" name="persist" value="true">
        <br><br>
        <input type="submit" value="Apply Change">
    </form>
    <p><a href="#" onclick="viewConfig()">View current configuration</a></p>
    <hr>

    <h2>4 - Save Redis Configuration to redis.conf</h2>
    <form id="save-config-form" action="/manager/save-config/" method="get">
        <label for="saveConfigNode">Select Node or "All Nodes":</label>
        <select id="saveConfigNode" name="redisNode">
            <option value="all">All Nodes</option>
            {''.join([f"<option value='{node}'>{node}</option>" for node in nodeList])}
        </select>
        <br><br>
        <input type="submit" value="Save Configuration">
    </form>
    <p><i>This will save the current Redis configuration to redis.conf file</i></p>
    <hr>

    <h2>5 - Rolling Restart</h2>
    <form id="rolling-restart-form" action="/manager/rolling-restart/" method="get">
        <label for="wait_minutes">Wait time between node restarts (minutes):</label>
        <input type="number" id="wait_minutes" name="wait_minutes" min="0" value="1">
        <br><br>
        <label for="restart_masters">Restart master nodes:</label>
        <input type="checkbox" id="restart_masters" name="restart_masters" value="true" checked>
        <br><br>
        <input type="submit" value="Start Rolling Restart">
    </form>
    <p><i>This will restart all slave nodes first, then master nodes if selected</i></p>
    <hr>

    <h2>6 - Command for all nodes</h2>
    <form id="execute-command-form" action="/manager/execute-command/" method="get">
        <label for="command">Redis Command:</label>
        <input type="text" id="command" name="command" placeholder="e.g., INFO MEMORY" required style="width: 300px;">
        <br><br>
        <label for="only_masters">Execute only on master nodes:</label>
        <input type="checkbox" id="only_masters" name="only_masters" value="true">
        <br><br>
        <label for="wait_seconds">Wait time between nodes (seconds):</label>
        <input type="number" id="wait_seconds" name="wait_seconds" min="0" value="0">
        <br><br>
        <input type="submit" value="Execute Command">
    </form>
    <p><i>This will execute the Redis command on selected nodes and display the results</i></p>
    <hr>

    <h2>7 - Show Redis Log File</h2>
    <form id="show-log-form" action="/manager/show-log/" method="get">
        <label for="logNode">Select Node:</label>
        <select id="logNode" name="redisNode">
            {''.join([f"<option value='{node}'>{node}</option>" for node in nodeList])}
        </select>
        <br><br>
        <label for="line_count">Number of lines to show:</label>
        <input type="number" id="line_count" name="line_count" min="10" max="10000" value="100">
        <br><br>
        <input type="submit" value="View Log File">
    </form>
    <p><i>This will display the Redis log file for the selected node</i></p>
    <hr>

    <script>
        // Handling the custom parameter input
        document.getElementById('custom-parameter').addEventListener('input', function(e) {{
            // If user types in the custom field, update the select dropdown
            if (e.target.value) {{
                document.getElementById('parameter').value = e.target.value;
            }}
        }});

        document.getElementById('parameter').addEventListener('change', function(e) {{
            // If user selects from dropdown, clear the custom field
            document.getElementById('custom-parameter').value = '';
        }});

        // Function to view configuration for a node
        function viewConfig() {{
            const node = document.getElementById('configNode').value;
            if (node) {{
                window.location.href = `/manager/get-config/?redisNode=${{node}}`;
            }} else {{
                alert('Please select a node first.');
            }}
        }}
        
        // Capture form submission and navigate to the corresponding endpoint
        document.getElementById('node-action-form').addEventListener('submit', function(event) {{
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
        
        // Similarly for the change-config form, ensure we use the parameter from either the dropdown or custom input
        document.getElementById('change-config-form').addEventListener('submit', function(event) {{
            event.preventDefault();
            const formData = new FormData(this);
            const trimmedData = {{}};
            
            for (const [key, value] of formData.entries()) {{
                if (key !== 'parameter') {{ // Handle parameter separately
                    trimmedData[key] = value.trim();
                }}
            }}
            
            // Get the parameter from either the dropdown or custom input
            const selectedParam = document.getElementById('parameter').value;
            const customParam = document.getElementById('custom-parameter').value;
            trimmedData['parameter'] = customParam || selectedParam;
            
            if (!trimmedData['parameter']) {{
                alert('Please select or enter a parameter.');
                return;
            }}
            
            if (!trimmedData['value']) {{
                alert('Please enter a value for the parameter.');
                return;
            }}

            const url = this.getAttribute('action');
            const queryParams = new URLSearchParams(trimmedData).toString();
            const fullUrl = `${{url}}?${{queryParams}}`;
            window.location.href = fullUrl;
        }});
        
        // Capture form submission for save-config form
        document.getElementById('save-config-form').addEventListener('submit', function(event) {{
            event.preventDefault();
            const formData = new FormData(this);
            const trimmedData = {{}};
            
            for (const [key, value] of formData.entries()) {{
                trimmedData[key] = value.trim();
            }}
            
            const url = this.getAttribute('action');
            const queryParams = new URLSearchParams(trimmedData).toString();
            const fullUrl = `${{url}}?${{queryParams}}`;
            window.location.href = fullUrl;
        }});
        
        // Capture form submission for rolling-restart form
        document.getElementById('rolling-restart-form').addEventListener('submit', function(event) {{
            event.preventDefault();
            const formData = new FormData(this);
            const trimmedData = {{}};
            
            for (const [key, value] of formData.entries()) {{
                trimmedData[key] = value.trim();
            }}
            
            // Set restart_masters to false if not checked
            if (!formData.has('restart_masters')) {{
                trimmedData['restart_masters'] = 'false';
            }}
            
            const url = this.getAttribute('action');
            const queryParams = new URLSearchParams(trimmedData).toString();
            const fullUrl = `${{url}}?${{queryParams}}`;
            window.location.href = fullUrl;
        }});
        
        // Capture form submission for execute-command form
        document.getElementById('execute-command-form').addEventListener('submit', function(event) {{
            event.preventDefault();
            const formData = new FormData(this);
            const trimmedData = {{}};
            
            for (const [key, value] of formData.entries()) {{
                trimmedData[key] = value.trim();
            }}
            
            // Set only_masters to false if not checked
            if (!formData.has('only_masters')) {{
                trimmedData['only_masters'] = 'false';
            }}
            
            const url = this.getAttribute('action');
            const queryParams = new URLSearchParams(trimmedData).toString();
            const fullUrl = `${{url}}?${{queryParams}}`;
            window.location.href = fullUrl;
        }});
        
        // Capture form submission for show-log form
        document.getElementById('show-log-form').addEventListener('submit', function(event) {{
            event.preventDefault();
            const formData = new FormData(this);
            const trimmedData = {{}};
            
            for (const [key, value] of formData.entries()) {{
                trimmedData[key] = value.trim();
            }}
            
            const url = this.getAttribute('action');
            const queryParams = new URLSearchParams(trimmedData).toString();
            const fullUrl = `${{url}}?${{queryParams}}`;
            window.location.href = fullUrl;
        }});
    </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# #############################################
# Maintenance Section
# #############################################

@app.get("/maintain/add-node/", response_class=HTMLResponse)
async def add_node(
    serverIP: str,
    serverPORT: str,
    maxMemSize: str,
    cpuCoreIDs: str,
    nodeType: str = "slave",
    masterID: str = "",
    confirmed: bool = False
):
    """
    Endpoint to add a new Redis node to the cluster.
    """
    if not validIP(serverIP):
        return HTMLResponse(content=f"""
        {css_style}
        <html><head><title>Error</title></head>
        <body>
            <h2>Invalid IP Address</h2>
            <p style='color: red;'>The IP address {serverIP} is not valid.</p>
            <div class="nav-buttons">
                <a href="/maintain">Back to Maintenance</a>
            </div>
        </body></html>
        """)

    # Ensure a master ID is provided for slave nodes
    if nodeType == 'slave-specific' and (not masterID or masterID.strip() == ""):
        return HTMLResponse(content=f"""
        {css_style}
        <html><head><title>Error</title></head>
        <body>
            <h2>Missing Master ID</h2>
            <p style='color: red;'>When adding a slave node, a master node ID must be provided.</p>
            <p>Please use the "View Master Nodes" button to select a valid master ID.</p>
            <div class="nav-buttons">
                <a href="/maintain">Back to Maintenance</a>
                <a href="/maintain/view-master-nodes" target="_blank">View Master Nodes</a>
            </div>
        </body></html>
        """)

    # Call add_delete_node_wv with proper parameters
    node_info = {
        'serverIP': serverIP,
        'serverPORT': serverPORT,
        'maxMemSize': maxMemSize,
        'cpuCoreIDs': cpuCoreIDs,
        'nodeType': nodeType,
        'masterID': masterID
    }

    result_html = add_delete_node_wv('add', node_info)

    # Construct the response message
    response_message = f"""
    {css_style}
    <html>
    <head><title>Add Redis Node</title></head>
    <body>
        <h2>Add Redis Node Result</h2>
        <div>{result_html}</div>
        <div class="nav-buttons">
            <a href="/maintain">Back to Maintenance</a>
            <a href="/maintain/view-master-nodes" target="_blank">View Master Nodes</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=response_message)

@app.get("/maintain/delete-node/", response_class=HTMLResponse)
async def delete_node(nodeId: str, confirmed: bool = False):
    """
    Endpoint to delete a Redis node from the cluster.
    """
    try:
        if not confirmed:
            # First verify the node exists and is active before showing confirmation
            try:
                node_id_int = int(nodeId)
                if node_id_int < 1 or node_id_int > len(pareNodes):
                    return HTMLResponse(content=f"""
                    {css_style}
                    <html>
                    <head><title>Error</title></head>
                    <body>
                        <h2>Invalid Node ID</h2>
                        <p style='color: red;'>Node ID {nodeId} doesn't exist. Valid range is 1-{len(pareNodes)}</p>
                        <div class="nav-buttons">
                            <a href="/maintain">Back to Maintenance</a>
                        </div>
                    </body>
                    </html>
                    """)

                if not pareNodes[node_id_int - 1][4]:
                    return HTMLResponse(content=f"""
                    {css_style}
                    <html>
                    <head><title>Error</title></head>
                    <body>
                        <h2>Inactive Node</h2>
                        <p style='color: red;'>Node {nodeId} is already marked as inactive</p>
                        <div class="nav-buttons">
                            <a href="/maintain">Back to Maintenance</a>
                        </div>
                    </body>
                    </html>
                    """)

                # Get node details for display
                serverIP = pareNodes[node_id_int - 1][0][0]
                serverPORT = pareNodes[node_id_int - 1][1][0]

                # Show confirmation page with node details
                return HTMLResponse(content=f"""
                {css_style}
                <html>
                <head><title>Confirm Delete Node</title></head>
                <body>
                    <h2>Confirm Node Deletion</h2>
                    <div class="confirmation-needed">
                        <p>Are you sure you want to delete this node from the cluster?</p>
                        <p><strong>Node:</strong> {nodeId} - {serverIP}:{serverPORT}</p>
                        <p style='color: red;'>This operation cannot be undone!</p>
                        <form action="/maintain/delete-node/" method="get">
                            <input type="hidden" name="nodeId" value="{nodeId}">
                            <input type="hidden" name="confirmed" value="true">
                            <button type="submit" class="confirm-btn">Yes, Delete Node</button>
                            <a href="/maintain" class="cancel-btn">Cancel</a>
                        </form>
                    </div>
                </body>
                </html>
                """)
            except Exception as e:
                return HTMLResponse(content=f"""
                {css_style}
                <html>
                <head><title>Error</title></head>
                <body>
                    <h2>Error Processing Node</h2>
                    <p style='color: red;'>An error occurred while processing node {nodeId}: {str(e)}</p>
                    <div class="nav-buttons">
                        <a href="/maintain">Back to Maintenance</a>
                    </div>
                </body>
                </html>
                """)

        # If confirmed, delegate to the add_delete_node_wv function
        result_html = add_delete_node_wv('del', nodeId)

        # Construct the response message
        response_message = f"""
        {css_style}
        <html>
        <head><title>Delete Redis Node</title></head>
        <body>
            <h2>Delete Node Result</h2>
            <div>{result_html}</div>
            <div class="nav-buttons">
                <a href="/maintain">Back to Maintenance</a>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=response_message)
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return HTMLResponse(content=f"""
        {css_style}
        <html>
        <head><title>Error</title></head>
        <body>
            <h2>Unexpected Error</h2>
            <p style='color: red;'>An unexpected error occurred: {str(e)}</p>
            <pre style='background-color: #f8f8f8; padding: 10px; overflow-x: auto; font-size: 12px;'>{trace}</pre>
            <div class="nav-buttons">
                <a href="/maintain">Back to Maintenance</a>
            </div>
        </body>
        </html>
        """)

@app.get("/maintain/view-master-nodes", response_class=HTMLResponse)
async def view_master_nodes():
    """
    Displays a list of master nodes with their IDs for adding slaves to specific masters.
    """
    master_nodes = []

    try:
        # Find a contact node to query cluster info
        contact_node = None
        for pareNode in pareNodes:
            if pareNode[4]:  # If active
                nodeIP = pareNode[0][0]
                portNumber = pareNode[1][0]
                if pingredisNode(nodeIP, portNumber):
                    contact_node = (nodeIP, portNumber)
                    break

        if not contact_node:
            return """
            <html>
            <head>
                <title>Master Nodes</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; }
                    .error { color: red; }
                </style>
            </head>
            <body>
                <h1>Master Nodes</h1>
                <p class="error">Error: Could not find any active node to query cluster information</p>
                <a href="/maintain">Back to Maintenance</a>
            </body>
            </html>
            """

        # Query the cluster for master nodes
        cmd_status, cmd_output = subprocess.getstatusoutput(
            redisConnectCmd(contact_node[0], contact_node[1], ' CLUSTER NODES | grep master'))

        if cmd_status != 0:
            return """
            <html>
            <head>
                <title>Master Nodes</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; }
                    .error { color: red; }
                </style>
            </head>
            <body>
                <h1>Master Nodes</h1>
                <p class="error">Error: Failed to get cluster nodes information</p>
                <a href="/maintain">Back to Maintenance</a>
            </body>
            </html>
            """

        lines = cmd_output.strip().split('\n')
        for line in lines:
            parts = line.split()
            if len(parts) >= 9 and "master" in line and "fail" not in line:
                node_id = parts[0]
                ip_port = parts[1]
                slots_info = " ".join(parts[8:]) if len(parts) > 8 else "No slots"
                master_nodes.append((node_id, ip_port, slots_info))

        # Generate HTML
        html_content = f"""
        {css_style}
        <html>
        <head>
            <title>Master Nodes</title>
        </head>
        <body>
            <h1>Master Nodes</h1>
            <p>Click on a node ID to copy it to clipboard</p>
            <table class="config-table" border="1">
                <thead>
                    <tr>
                        <th>Node ID</th>
                        <th>IP:Port</th>
                        <th>Slots</th>
                    </tr>
                </thead>
                <tbody>
        """

        for node in master_nodes:
            html_content += f"""
                    <tr>
                        <td><a href="#" class="node-id" data-id="{node[0]}" onclick="copyToClipboard('{node[0]}')">{node[0]}</a></td>
                        <td>{node[1]}</td>
                        <td>{node[2]}</td>
                    </tr>
            """

        html_content += """
                </tbody>
            </table>
            <div id="copy-message" style="display:none; padding: 10px; margin-top: 10px; background-color: #dff0d8; color: #3c763d; border: 1px solid #d6e9c6; border-radius: 4px;">
                Node ID copied to clipboard!
            </div>
            <div style="margin-top: 20px">
                <a href="/maintain" class="btn">Back to Maintenance</a>
            </div>
            <script>
                function copyToClipboard(text) {
                    var textarea = document.createElement("textarea");
                    textarea.value = text;
                    document.body.appendChild(textarea);
                    textarea.select();
                    document.execCommand("copy");
                    document.body.removeChild(textarea);
                    
                    // Show copy message
                    var message = document.getElementById("copy-message");
                    message.style.display = "block";
                    setTimeout(function() {
                        message.style.display = "none";
                    }, 2000);
                }
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    except Exception as e:
        return f"""
        <html>
        <head>
            <title>Master Nodes</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                .error {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Master Nodes</h1>
            <p class="error">Error: {str(e)}</p>
            <a href="/maintain">Back to Maintenance</a>
        </body>
        </html>
        """

@app.get("/maintain", response_class=HTMLResponse)
async def maintain():
    """
    Displays the Redis Cluster Maintenance UI.
    """
    # Ensure we have the latest node list
    import importlib
    importlib.reload(sys.modules['pareNodeList'])
    from pareNodeList import pareNodes as fresh_pareNodes

    # Update the global pareNodes
    global pareNodes
    pareNodes = fresh_pareNodes

    nodeList = getNodeList()
    # Get active nodes for deletion dropdown
    active_nodes_with_id = []
    for i, pareNode in enumerate(pareNodes, start=1):
        if pareNode[4]:  # If active
            nodeIP = pareNode[0][0]
            portNumber = pareNode[1][0]
            active_nodes_with_id.append((i, f"{nodeIP}:{portNumber}"))

    # Generate the HTML content for the maintenance page
    html_content = f"""
    {css_style}
    <html>
    <head>
        <title>Redis Cluster Maintenance</title>
        <style>
            .form-section {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 15px;
            }}
            .form-row {{
                margin-bottom: 10px;
            }}
            .tab-content {{
                display: none;
                padding: 15px;
                border: 1px solid #ddd;
            }}
            .active-tab {{
                display: block;
            }}
        </style>
    </head>
    <body>
    <h1>Redis Cluster Maintenance (paredicmaint)</h1>
    <div class="nav-buttons">
        <a href="/monitor">Go to Monitor (paredicmon)</a>
        <a href="/manager">Go to Manager (paredicman)</a>
    </div>
    <hr>

    <h2>1 - Add/Delete Redis Node</h2>
    <div>
        <div class="tab-navigation">
            <button onclick="showTab('add-node')">Add Node</button>
            <button onclick="showTab('delete-node')">Delete Node</button>
        </div>

        <div id="add-node" class="tab-content active-tab">
            <h3>Add a New Redis Node</h3>
            <div class="form-section">
                <form id="add-node-form" action="/maintain/add-node/" method="get">
                    <div class="form-row">
                        <label for="serverIP">Server IP:</label>
                        <input type="text" id="serverIP" name="serverIP" required 
                               placeholder="e.g., 192.168.1.10">
                    </div>
                    <div class="form-row">
                        <label for="serverPORT">Port Number:</label>
                        <input type="number" id="serverPORT" name="serverPORT" required 
                               placeholder="e.g., 6379">
                    </div>
                    <div class="form-row">
                        <label for="maxMemSize">Maximum Memory:</label>
                        <input type="text" id="maxMemSize" name="maxMemSize" required 
                               placeholder="e.g., 2gb or 500mb">
                    </div>
                    <div class="form-row">
                        <label for="cpuCoreIDs">CPU Core IDs:</label>
                        <input type="text" id="cpuCoreIDs" name="cpuCoreIDs" required 
                               placeholder="e.g., 1 or 1,2,3">
                    </div>
                    <div class="form-row">
                        <label for="nodeType">Node Type:</label>
                        <select id="nodeType" name="nodeType" onchange="toggleMasterIdField()">
                            <option value="master">Master Node</option>
                            <option value="slave-specific">Slave Node</option>
                        </select>
                    </div>
                    <div id="masterIdField" class="form-row" style="display: none;">
                        <label for="masterID">Master Node ID:</label>
                        <input type="text" id="masterID" name="masterID" placeholder="Enter master node ID">
                        <button type="button" onclick="window.open('/maintain/view-master-nodes', '_blank')">
                            View Master Nodes
                        </button>
                    </div>
                    <div class="form-row">
                        <input type="submit" value="Add Node">
                    </div>
                </form>
            </div>
        </div>

        <div id="delete-node" class="tab-content">
            <h3>Delete a Redis Node</h3>
            <div class="form-section">
                <form id="delete-node-form" action="/maintain/delete-node/" method="get">
                    <div class="form-row">
                        <label for="nodeId">Select Node to Delete:</label>
                        <select id="nodeId" name="nodeId" required>
                            {''.join([f"<option value='{id}'>{id} - {node}</option>" for id, node in active_nodes_with_id])}
                        </select>
                    </div>
                    <div class="form-row">
                        <input type="submit" value="Delete Node">
                    </div>
                </form>
            </div>
        </div>
    </div>
    <hr>

    <h2>2 - Move Slot(s)</h2>
    <p><i>(Not Implemented Yet)</i></p>
    <hr>

    <h2>3 - Redis Cluster Nodes Version Upgrade</h2>
    <p><i>(Not Implemented Yet)</i></p>
    <hr>

    <h2>4 - Redis Cluster Nodes Version Control</h2>
    <p><i>(Not Implemented Yet)</i></p>
    <hr>

    <h2>5 - Maintain Server</h2>
    <p><i>(Not Implemented Yet)</i></p>
    <hr>

    <h2>6 - Migrate Data From Remote Redis</h2>
    <p><i>(Not Implemented Yet)</i></p>
    <hr>

    <h2>7 - Cluster Slot(load) Balancer</h2>
    <p><i>(Not Implemented Yet)</i></p>
    <hr>

    <script>
        function showTab(tabId) {{
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.remove('active-tab');
            }});
            // Show selected tab
            document.getElementById(tabId).classList.add('active-tab');
        }}

        function toggleMasterIdField() {{
            const nodeType = document.getElementById('nodeType').value;
            const masterIdField = document.getElementById('masterIdField');
            masterIdField.style.display = nodeType === 'slave-specific' ? 'block' : 'none';
        }}

        // Form validation and submission
        document.getElementById('add-node-form').addEventListener('submit', function(e) {{
            e.preventDefault();
            const formData = new FormData(this);
            
            // Additional validation
            const maxMemSize = formData.get('maxMemSize');
            if (!maxMemSize.match(/^\\d+[mg]b$/i)) {{
                alert('Memory size must be in format: NUMBER[mg]b (e.g., 2gb or 500mb)');
                return;
            }}

            const cpuCoreIDs = formData.get('cpuCoreIDs');
            if (!cpuCoreIDs.match(/^\\d+(?:,\\d+)*$/)) {{
                alert('CPU Core IDs must be numbers separated by commas');
                return;
            }}

            // Validate master ID for slave nodes
            const nodeType = formData.get('nodeType');
            const masterID = formData.get('masterID');
            if (nodeType === 'slave-specific' && (!masterID || masterID.trim().length === 0)) {{
                alert('Master Node ID is required when adding a slave node');
                return;
            }}

            // Build URL with parameters
            const url = this.getAttribute('action');
            const params = new URLSearchParams(formData);
            window.location.href = `${{url}}?${{params.toString()}}`;
        }});

        document.getElementById('delete-node-form').addEventListener('submit', function(e) {{
            e.preventDefault();
            const formData = new FormData(this);
            const url = this.getAttribute('action');
            const params = new URLSearchParams(formData);
            window.location.href = `${{url}}?${{params.toString()}}`;
        }});
    </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# #############################################

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=(pareServerIp), port=(pareWebPort))



