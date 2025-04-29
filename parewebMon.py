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



# Define the CSS styles for different button types
css_style = """
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            margin: 20px;
        }
        h1 {
            color: #ffffff;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
        .monitor-title {
            background-color: #4f4f4f; /* Dark gray */
        }
        .manager-title {
            background-color: #001f3f; /* Navy blue */
        }
        .maintenance-title {
            background-color: #800000; /* Claret */
        }
        th {
            text-align: left;
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
            width: 150px;
            margin-right: 10px;
        }
        input[type="text"], select {
            width: 160px;
            padding: 5px;
            border: 1px solid #cccccc;
            border-radius: 5px;
        }
        /* Dark gray buttons for monitor page */
        .monitor-button, .monitor-button input[type="submit"], .monitor-nav {
            padding: 10px 15px;
            background-color: #4f4f4f; /* Dark gray */
            color: #ffffff;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-align: center;
            display: inline-block;
            vertical-align: middle;
            text-decoration: none;
        }
        .monitor-button:hover, .monitor-button input[type="submit"]:hover, .monitor-nav:hover {
            background-color: #3f3f3f; /* Slightly darker gray */
        }
        /* Navy blue buttons for manager page */
        .manager-button, .manager-button input[type="submit"], .manager-nav {
            padding: 10px 15px;
            background-color: #001f3f; /* Navy blue */
            color: #ffffff;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-align: center;
            display: inline-block;
            vertical-align: middle;
            text-decoration: none;
        }
        .manager-button:hover, .manager-button input[type="submit"]:hover, .manager-nav:hover {
            background-color: #001a35; /* Slightly darker navy blue */
        }
        /* Claret buttons for maintenance page */
        .maintenance-button, .maintenance-button input[type="submit"], .maintenance-nav {
            padding: 10px 15px;
            background-color: #800000; /* Claret */
            color: #ffffff;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-align: center;
            display: inline-block;
            vertical-align: middle;
            text-decoration: none;
        }
        .maintenance-button:hover, .maintenance-button input[type="submit"]:hover, .maintenance-nav:hover {
            background-color: #660000; /* Slightly darker claret */
        }
        .collapsible {
            background-color: #f1f1f1;
            color: #333;
            cursor: pointer;
            padding: 10px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-size: 16px;
            margin-bottom: 5px;
        }
        .active, .collapsible:hover {
            background-color: #ddd;
        }
        .content {
            padding: 15px;
            display: none;
            overflow: hidden;
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            margin-bottom: 10px;
        }
        .content > * {
            margin-bottom: 10px;
        }
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }
        .form-group {
            display: flex;
            flex-direction: column;
        }
        .form-group.full-width {
            grid-column: span 2;
        }
        .button-container {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .button-container > * {
            margin: 0;
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
    """
    Displays the Redis Cluster Monitoring UI with collapsible sections.
    """
    # Reload the pareNodes configuration to ensure the latest node list
    import importlib
    importlib.reload(sys.modules['pareNodeList'])
    from pareNodeList import pareNodes as fresh_pareNodes

    # Update the global pareNodes
    global pareNodes
    pareNodes = fresh_pareNodes

    uniqueservers = getuniqueServers(pareNodes)
    commandsAvailable = ['server', 'clients', 'memory', 'persistence', 'stats', 'replication', 'cpu', 'cluster']
    nodeList = getNodeList()

    # Generate the HTML content for the monitoring page
    html_content = f"""
    {css_style}
    <html>
    <head>
        <title>Redis Cluster Monitor</title>
    </head>
    <body>
    <h1 class="monitor-title">Redis Cluster Monitor</h1>
    <div class="nav-buttons">
        <a href="/manager" class="manager-nav">Go to Manager</a>
        <a href="/maintain" class="maintenance-nav">Go to Maintenance</a>
    </div>
    <hr>

    <button class="collapsible">1 - Ping Nodes</button>
    <div class="content">
        <div class="button-container">
            <button class="monitor-button" onclick="fetchPingNodes()">Ping Nodes</button>
        </div>
        <div id="ping-nodes-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">2 - List Nodes</button>
    <div class="content">
        <div class="button-container">
            <button class="monitor-button" onclick="fetchListNodes()">List Nodes</button>
        </div>
        <div id="list-nodes-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">3 - Node Info</button>
    <div class="content">
        <form id="node-info-form" onsubmit="fetchNodeInfo(event)">
            <div class="button-container">
                <label for="redisNode">Redis Node:</label>
                <select id="redisNode" name="redisNode" onchange="fetchNodeInfo(new Event('submit', {{cancelable: true}}))">
                    {''.join([f"<option value='{node}'>{node}</option>" for node in nodeList])}
                </select>
            </div>
            <div class="button-container" style="margin-top: 10px;">
                <label for="command">Command:</label>
                <select id="command" name="command" onchange="fetchNodeInfo(new Event('submit', {{cancelable: true}}))">
                    {''.join([f"<option value='{command}'>{command}</option>" for command in commandsAvailable])}
                </select>
            </div>
        </form>
        <div id="node-info-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">4 - Server Info</button>
    <div class="content">
        <form id="server-info-form" onsubmit="fetchServerInfo(event)">
            <div class="button-container">
                <input class="monitor-button" type="submit" value="Get Info">
                <label for="server_ip">Server IP:</label>
                <select id="server_ip" name="server_ip">
                    {''.join([f"<option value='{server}'>{server}</option>" for server in uniqueservers])}
                </select>
            </div>
        </form>
        <div id="server-info-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">5 - Slot Info</button>
    <div class="content">
        <div class="button-container">
            <button class="monitor-button" onclick="fetchSlotInfo()">Get Slot Info</button>
        </div>
        <div id="slot-info-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">6 - Cluster State Info</button>
    <div class="content">
        <div class="button-container">
            <button class="monitor-button" onclick="fetchClusterStateInfo()">Get Cluster State Info</button>
        </div>
        <div id="cluster-state-info-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">7 - Memory Usage</button>
    <div class="content">
        <div class="button-container">
            <button class="monitor-button" onclick="fetchMemoryUsage()">Get Memory Usage</button>
        </div>
        <div id="memory-usage-result" style="margin-top: 10px;"></div>
    </div>

    <script>
        const collapsibles = document.querySelectorAll(".collapsible");
        collapsibles.forEach(button => {{
            button.addEventListener("click", function() {{
                this.classList.toggle("active");
                const content = this.nextElementSibling;
                if (content.style.display === "block") {{
                    content.style.display = "none";
                }} else {{
                    content.style.display = "block";
                }}
            }});
        }});

        function fetchPingNodes() {{
            fetch('/monitor/ping-nodes/')
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('ping-nodes-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById('ping-nodes-result').innerHTML = "<p style='color: red;'>Error fetching ping nodes: " + error + "</p>";
                }});
        }}

        function fetchListNodes() {{
            fetch('/monitor/list-nodes/')
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('list-nodes-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById('list-nodes-result').innerHTML = "<p style='color: red;'>Error fetching list nodes: " + error + "</p>";
                }});
        }}

        function fetchNodeInfo(event) {{
            event.preventDefault();
            const formData = new FormData(document.getElementById('node-info-form'));
            const params = new URLSearchParams(formData).toString();
            
            document.getElementById('node-info-result').innerHTML = "<p>Loading...</p>";
            
            fetch('/monitor/node-info/?' + params)
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('node-info-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById('node-info-result').innerHTML = "<p style='color: red;'>Error fetching node info: " + error + "</p>";
                }});
        }}

        function fetchServerInfo(event) {{
            event.preventDefault();
            const formData = new FormData(document.getElementById('server-info-form'));
            const params = new URLSearchParams(formData).toString();
            fetch('/monitor/server-info/?' + params)
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('server-info-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById('server-info-result').innerHTML = "<p style='color: red;'>Error fetching server info: " + error + "</p>";
                }});
        }}

        function fetchSlotInfo() {{
            fetch('/monitor/slot-info/')
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('slot-info-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById('slot-info-result').innerHTML = "<p style='color: red;'>Error fetching slot info: " + error + "</p>";
                }});
        }}

        function fetchClusterStateInfo() {{
            fetch('/monitor/cluster-state-info/')
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('cluster-state-info-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById('cluster-state-info-result').innerHTML = "<p style='color: red;'>Error fetching cluster state info: " + error + "</p>";
                }});
        }}

        function fetchMemoryUsage() {{
            fetch('/monitor/memory-usage/')
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('memory-usage-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById('memory-usage-result').innerHTML = "<p style='color: red;'>Error fetching memory usage: " + error + "</p>";
                }});
        }}
    </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# #############################################
# Manager Section
# #############################################

@app.get("/manager", response_class=HTMLResponse)
async def manager():
    """
    Displays the Redis Cluster Manager UI with collapsible sections.
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
    <head>
        <title>Redis Cluster Manager</title>
    </head>
    <body>
    <h1 class="manager-title">Redis Cluster Manager</h1>
    <div class="nav-buttons">
        <a href="/monitor" class="monitor-nav">Go to Monitor</a>
        <a href="/maintain" class="maintenance-nav">Go to Maintenance</a>
    </div>
    <hr>

    <button class="collapsible">1 - Start/Stop/Restart Redis Node</button>
    <div class="content">
        <form id="node-action-form" onsubmit="performNodeAction(event)">
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
            <input class="manager-button" type="submit" value="Perform Action">
        </form>
        <div id="node-action-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">2 - Switch Master/Slave Nodes</button>
    <div class="content">
        <form id="switch-master-slave-form" onsubmit="switchMasterSlave(event)">
            <label for="masterNode">Select Master Node:</label>
            <select id="masterNode" name="redisNode">
                {''.join([f"<option value='{node}'>{node}</option>" for node in masterNodes])}
            </select>
            <br><br>
            <input class="manager-button" type="submit" value="Switch Master/Slave">
        </form>
        <div id="switch-master-slave-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">3 - Change Redis Configuration Parameter</button>
    <div class="content">
        <form id="change-config-form" onsubmit="changeConfig(event)">
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
            <label for="value">New Value:</label>
            <input type="text" id="value" name="value" placeholder="e.g., 2gb">
            <br><br>
            <label for="persist">Persist to config:</label>
            <input type="checkbox" id="persist" name="persist" value="true">
            <br><br>
            <input class="manager-button" type="submit" value="Apply Change">
        </form>
        <div id="change-config-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">4 - Save Redis Configuration to redis.conf</button>
    <div class="content">
        <form id="save-config-form" onsubmit="saveConfig(event)">
            <label for="saveConfigNode">Select Node or "All Nodes":</label>
            <select id="saveConfigNode" name="redisNode">
                <option value="all">All Nodes</option>
                {''.join([f"<option value='{node}'>{node}</option>" for node in nodeList])}
            </select>
            <br><br>
            <input class="manager-button" type="submit" value="Save Configuration">
        </form>
        <div id="save-config-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">5 - Rolling Restart</button>
    <div class="content">
        <form id="rolling-restart-form" onsubmit="rollingRestart(event)">
            <label for="wait_minutes">Wait time between node restarts (minutes):</label>
            <input type="number" id="wait_minutes" name="wait_minutes" min="0" value="1">
            <br><br>
            <label for="restart_masters">Restart master nodes:</label>
            <input type="checkbox" id="restart_masters" name="restart_masters" value="true" checked>
            <br><br>
            <input class="manager-button" type="submit" value="Start Rolling Restart">
        </form>
        <div id="rolling-restart-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">6 - Command for all nodes</button>
    <div class="content">
        <form id="execute-command-form" onsubmit="executeCommand(event)">
            <label for="command">Redis Command:</label>
            <input type="text" id="command" name="command" placeholder="e.g., INFO MEMORY" required style="width: 300px;">
            <br><br>
            <label for="only_masters">Execute only on master nodes:</label>
            <input type="checkbox" id="only_masters" name="only_masters" value="true">
            <br><br>
            <label for="wait_seconds">Wait time between nodes (seconds):</label>
            <input type="number" id="wait_seconds" name="wait_seconds" min="0" value="0">
            <br><br>
            <input class="manager-button" type="submit" value="Execute Command">
        </form>
        <div id="execute-command-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">7 - Show Redis Log File</button>
    <div class="content">
        <form id="show-log-form" onsubmit="showLog(event)">
            <label for="logNode">Select Node:</label>
            <select id="logNode" name="redisNode">
                {''.join([f"<option value='{node}'>{node}</option>" for node in nodeList])}
            </select>
            <br><br>
            <label for="line_count">Number of lines to show:</label>
            <input type="number" id="line_count" name="line_count" min="10" max="10000" value="100">
            <br><br>
            <input class="manager-button" type="submit" value="View Log File">
        </form>
        <div id="show-log-result" style="margin-top: 10px;"></div>
    </div>

    <script>
        const collapsibles = document.querySelectorAll(".collapsible");
        collapsibles.forEach(button => {{
            button.addEventListener("click", function() {{
                this.classList.toggle("active");
                const content = this.nextElementSibling;
                if (content.style.display === "block") {{
                    content.style.display = "none";
                }} else {{
                    content.style.display = "block";
                }}
            }});
        }});

        function performNodeAction(event) {{
            event.preventDefault();
            const formData = new FormData(document.getElementById('node-action-form'));
            const params = new URLSearchParams(formData).toString();
            fetch('/manager/node-action/?' + params)
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('node-action-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById('node-action-result').innerHTML = "<p style='color: red;'>Error performing action: " + error + "</p>";
                }});
        }}

        function switchMasterSlave(event) {{
            event.preventDefault();
            const formData = new FormData(document.getElementById('switch-master-slave-form'));
            const params = new URLSearchParams(formData).toString();
            fetch('/manager/switch-master-slave/?' + params)
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('switch-master-slave-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById('switch-master-slave-result').innerHTML = "<p style='color: red;'>Error switching master/slave: " + error + "</p>";
                }});
        }}

        function changeConfig(event) {{
            event.preventDefault();
            const formData = new FormData(document.getElementById('change-config-form'));
            const params = new URLSearchParams(formData).toString();
            fetch('/manager/change-config/?' + params)
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('change-config-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById('change-config-result').innerHTML = "<p style='color: red;'>Error changing config: " + error + "</p>";
                }});
        }}

        function saveConfig(event) {{
            event.preventDefault();
            const formData = new FormData(document.getElementById('save-config-form'));
            const params = new URLSearchParams(formData).toString();
            fetch('/manager/save-config/?' + params)
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('save-config-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById('save-config-result').innerHTML = "<p style='color: red;'>Error saving config: " + error + "</p>";
                }});
        }}

        function rollingRestart(event) {{
            event.preventDefault();
            const formData = new FormData(document.getElementById('rolling-restart-form'));
            const params = new URLSearchParams(formData).toString();
            fetch('/manager/rolling-restart/?' + params)
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('rolling-restart-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById('rolling-restart-result').innerHTML = "<p style='color: red;'>Error performing rolling restart: " + error + "</p>";
                }});
        }}

        function executeCommand(event) {{
            event.preventDefault();
            const formData = new FormData(document.getElementById('execute-command-form'));
            const params = new URLSearchParams(formData).toString();
            fetch('/manager/execute-command/?' + params)
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('execute-command-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById('execute-command-result').innerHTML = "<p style='color: red;'>Error executing command: " + error + "</p>";
                }});
        }}

        function showLog(event) {{
            event.preventDefault();
            const formData = new FormData(document.getElementById('show-log-form'));
            const params = new URLSearchParams(formData).toString();
            fetch('/manager/show-log/?' + params)
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('show-log-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById('show-log-result').innerHTML = "<p style='color: red;'>Error fetching log: " + error + "</p>";
                }});
        }}
    </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/manager/node-action/", response_class=HTMLResponse)
async def manager_node_action(redisNode: str, action: str, confirmed: bool = False):
    """
    Endpoint to perform start, stop, or restart actions on a Redis node.
    """
    try:
        result = node_action_wv(redisNode, action, confirmed)
        return HTMLResponse(content=result)
    except Exception as e:
        return HTMLResponse(content=f"<p style='color: red;'>Error: {str(e)}</p>")

@app.get("/manager/switch-master-slave/", response_class=HTMLResponse)
async def manager_switch_master_slave(redisNode: str):
    """
    Endpoint to switch roles between a master node and one of its slaves.
    """
    try:
        result = switch_master_slave_wv(redisNode)
        return HTMLResponse(content=result)
    except Exception as e:
        return HTMLResponse(content=f"<p style='color: red;'>Error: {str(e)}</p>")

@app.get("/manager/change-config/", response_class=HTMLResponse)
async def manager_change_config(redisNode: str, parameter: str, value: str, persist: bool = False):
    """
    Endpoint to change a Redis configuration parameter for a specific node.
    """
    try:
        result = change_config_wv(redisNode, parameter, value, persist)
        return HTMLResponse(content=result)
    except Exception as e:
        return HTMLResponse(content=f"<p style='color: red;'>Error: {str(e)}</p>")

@app.get("/manager/save-config/", response_class=HTMLResponse)
async def manager_save_config(redisNode: str):
    """
    Endpoint to save the Redis configuration to redis.conf for a specific node or all nodes.
    """
    try:
        result = save_config_wv(redisNode)
        return HTMLResponse(content=result)
    except Exception as e:
        return HTMLResponse(content=f"<p style='color: red;'>Error: {str(e)}</p>")

@app.get("/manager/rolling-restart/", response_class=HTMLResponse)
async def manager_rolling_restart(wait_minutes: int = 0, restart_masters: bool = True):
    """
    Endpoint to perform a rolling restart of Redis nodes.
    """
    try:
        result = rolling_restart_wv(wait_minutes, restart_masters)
        return HTMLResponse(content=result)
    except Exception as e:
        return HTMLResponse(content=f"<p style='color: red;'>Error: {str(e)}</p>")

@app.get("/manager/show-log/", response_class=HTMLResponse)
async def manager_show_log(redisNode: str, line_count: int = 100):
    """
    Endpoint to display the Redis log file for a specific node.
    """
    try:
        result = show_redis_log_wv(redisNode, line_count)
        return f"""
        {css_style}
        <html>
        <head><title>Show Redis Log</title></head>
        <body>
            <h2>Redis Log File</h2>
            <p>Node: {redisNode}</p>
            <p>Lines: {line_count}</p>
            {result}
        </body>
        </html>
        """
    except Exception as e:
        return f"""
        {css_style}
        <html>
        <head><title>Error</title></head>
        <body>
            <h2>Error</h2>
            <p style='color: red;'>Error: {str(e)}</p>
        </body>
        </html>
        """

@app.get("/manager/execute-command/", response_class=HTMLResponse)
async def manager_execute_command(command: str, only_masters: bool = False, wait_seconds: int = 0):
    """
    Endpoint to execute a Redis command on all nodes or only master nodes.
    """
    try:
        result = execute_command_wv(command, only_masters, wait_seconds)
        return f"""
        {css_style}
        <html>
        <head><title>Execute Command</title></head>
        <body>
            <h2>Command Execution Results</h2>
            <p>Command: {command}</p>
            <p>Only Masters: {"Yes" if only_masters else "No"}</p>
            <p>Wait Seconds: {wait_seconds}</p>
            {result}
        </body>
        </html>
        """
    except Exception as e:
        return f"""
        {css_style}
        <html>
        <head><title>Error</title></head>
        <body>
            <h2>Error</h2>
            <p style='color: red;'>Error: {str(e)}</p>
        </body>
        </html>
        """

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """
    Handle requests for the favicon.ico file to avoid 404 errors.
    """
    return Response(content="", media_type="image/x-icon")


# #############################################
# Maintenance Section
# #############################################

@app.get("/maintain", response_class=HTMLResponse)
async def maintain():
    """
    Displays the Redis Cluster Maintenance UI with collapsible sections.
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
    </head>
    <body>
    <h1 class="maintenance-title">Redis Cluster Maintenance</h1>
    <div class="nav-buttons">
        <a href="/monitor" class="monitor-nav">Go to Monitor</a>
        <a href="/manager" class="manager-nav">Go to Manager</a>
    </div>
    <hr>

    <button class="collapsible">1 - Add/Delete Redis Node</button>
    <div class="content">
        <h3>Add a New Redis Node</h3>
        <form id="add-node-form" onsubmit="addNode(event)">
            <div style="display: flex; align-items: center; gap: 10px;">
                <label for="serverIP" style="width: 150px;">Server IP:</label>
                <input type="text" id="serverIP" name="serverIP" required placeholder="e.g., 192.168.1.10">
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <label for="serverPORT" style="width: 150px;">Port Number:</label>
                <input type="number" id="serverPORT" name="serverPORT" required placeholder="e.g., 6379">
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <label for="maxMemSize" style="width: 150px;">Maximum Memory:</label>
                <input type="text" id="maxMemSize" name="maxMemSize" required placeholder="e.g., 2gb or 500mb">
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <label for="cpuCoreIDs" style="width: 150px;">CPU Core IDs:</label>
                <input type="text" id="cpuCoreIDs" name="cpuCoreIDs" required placeholder="e.g., 1 or 1,2,3">
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <label for="nodeType" style="width: 150px;">Node Type:</label>
                <select id="nodeType" name="nodeType" onchange="toggleMasterDropdown()">
                    <option value="master">Master Node</option>
                    <option value="slave-specific">Slave Node</option>
                </select>
            </div>
            <div id="masterDropdownField" style="display: none; flex; align-items: center; gap: 10px;">
                <label for="masterID" style="width: 150px;">Master Node:</label>
                <select id="masterID" name="masterID">
                    <option value="">Loading...</option>
                </select>
            </div>
            <div style="display: flex; justify-content: flex-start;">
                <input class="maintenance-button" type="submit" value="Add Node" style="width: auto;">
            </div>
        </form>
        <div id="add-node-result" style="margin-top: 10px;"></div>

        <h3>Delete a Redis Node</h3>
        <form id="delete-node-form" onsubmit="deleteNode(event)">
            <div style="display: flex; align-items: center; gap: 10px;">
                <select id="nodeId" name="nodeId" required>
                    {''.join([f"<option value='{id}'>{id} - {node}</option>" for id, node in active_nodes_with_id])}
                </select>
                <input class="maintenance-button" type="submit" value="Delete Node" style="width: auto; background-color: #d9534f; color: white;">
            </div>
        </form>
        <div id="delete-node-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">2 - Move Slot(s)</button>
    <div class="content">
        <div style="text-align: center; padding: 20px; color: #888;">
            <p><i class="fas fa-tools"></i> This feature is not implemented yet.</p>
            <p>Move slots between Redis master nodes to rebalance your cluster.</p>
            <button onclick="fetchNotImplemented('move-slots')" class="btn-disabled">Move Slots</button>
        </div>
        <div id="move-slots-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">3 - Redis Cluster Nodes Version Upgrade</button>
    <div class="content">
        <div style="text-align: center; padding: 20px; color: #888;">
            <p><i class="fas fa-tools"></i> This feature is not implemented yet.</p>
            <p>Upgrade Redis nodes to a newer version with minimal downtime.</p>
            <button onclick="fetchNotImplemented('version-upgrade')" class="btn-disabled">Version Upgrade</button>
        </div>
        <div id="version-upgrade-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">4 - Redis Cluster Nodes Version Control</button>
    <div class="content">
        <div style="text-align: center; padding: 20px; color: #888;">
            <p><i class="fas fa-tools"></i> This feature is not implemented yet.</p>
            <p>Check and control Redis versions across your cluster.</p>
            <button onclick="fetchNotImplemented('version-control')" class="btn-disabled">Version Control</button>
        </div>
        <div id="version-control-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">5 - Maintain Server</button>
    <div class="content">
        <div style="text-align: center; padding: 20px; color: #888;">
            <p><i class="fas fa-tools"></i> This feature is not implemented yet.</p>
            <p>Perform server maintenance operations.</p>
            <button onclick="fetchNotImplemented('server-maintain')" class="btn-disabled">Maintain Server</button>
        </div>
        <div id="server-maintain-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">6 - Migrate Data From Remote Redis</button>
    <div class="content">
        <div style="text-align: center; padding: 20px; color: #888;">
            <p><i class="fas fa-tools"></i> This feature is not implemented yet.</p>
            <p>Migrate data from a remote Redis instance to this cluster.</p>
            <button onclick="fetchNotImplemented('migrate-data')" class="btn-disabled">Migrate Data</button>
        </div>
        <div id="migrate-data-result" style="margin-top: 10px;"></div>
    </div>

    <button class="collapsible">7 - Cluster Slot(load) Balancer</button>
    <div class="content">
        <div style="text-align: center; padding: 20px; color: #888;">
            <p><i class="fas fa-tools"></i> This feature is not implemented yet.</p>
            <p>Balance slot distribution across your Redis cluster.</p>
            <button onclick="fetchNotImplemented('slot-balancer')" class="btn-disabled">Balance Slots</button>
        </div>
        <div id="slot-balancer-result" style="margin-top: 10px;"></div>
    </div>

    <script>
        const collapsibles = document.querySelectorAll(".collapsible");
        collapsibles.forEach(button => {{
            button.addEventListener("click", function() {{
                this.classList.toggle("active");
                const content = this.nextElementSibling;
                if (content.style.display === "block") {{
                    content.style.display = "none";
                }} else {{
                    content.style.display = "block";
                }}
            }});
        }});

        function toggleMasterDropdown() {{
            const nodeType = document.getElementById('nodeType').value;
            const masterDropdownField = document.getElementById('masterDropdownField');
            if (nodeType === 'slave-specific') {{
                masterDropdownField.style.display = 'flex';
                fetch('/maintain/view-master-nodes-dropdown')
                    .then(response => response.text())
                    .then(data => {{
                        document.getElementById('masterID').innerHTML = data;
                    }})
                    .catch(error => {{
                        console.error('Error fetching master nodes:', error);
                        document.getElementById('masterID').innerHTML = "<option value=''>Error loading master nodes</option>";
                    }});
            }} else {{
                masterDropdownField.style.display = 'none';
            }}
        }}

        function addNode(event) {{
            event.preventDefault();
            const formData = new FormData(document.getElementById('add-node-form'));
            const params = new URLSearchParams(formData).toString();
            fetch('/maintain/add-node/?' + params)
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('add-node-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById('add-node-result').innerHTML = "<p style='color: red;'>Error adding node: " + error + "</p>";
                }});
        }}

        function deleteNode(event) {{
            event.preventDefault();
            const formData = new FormData(document.getElementById('delete-node-form'));
            const params = new URLSearchParams(formData).toString();
            
            // Show loading indicator
            document.getElementById('delete-node-result').innerHTML = "<p>Loading...</p>";
            
            fetch('/maintain/delete-node/?' + params)
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('delete-node-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById('delete-node-result').innerHTML = "<p style='color: red;'>Error deleting node: " + error + "</p>";
                }});
        }}
        
        function confirmDeleteNode(nodeId) {{
            // Show loading indicator
            document.getElementById('delete-node-result').innerHTML = "<p>Deleting node...</p>";
            
            fetch('/maintain/delete-node/?nodeId=' + nodeId + '&confirmed=true')
                .then(response => response.text())
                .then(data => {{
                    document.getElementById('delete-node-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById('delete-node-result').innerHTML = "<p style='color: red;'>Error during node deletion: " + error + "</p>";
                }});
        }}
        
        function cancelDeleteNode() {{
            document.getElementById('delete-node-result').innerHTML = "<p>Node deletion cancelled.</p>";
        }}
        
        function fetchNotImplemented(feature) {{
            fetch('/maintain/' + feature + '/')
                .then(response => response.text())
                .then(data => {{
                    document.getElementById(feature + '-result').innerHTML = data;
                }})
                .catch(error => {{
                    document.getElementById(feature + '-result').innerHTML = "<p style='color: red;'>Error: " + error + "</p>";
                }});
        }}
    </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/maintain/add-node/", response_class=HTMLResponse)
async def add_node(
    serverIP: str,
    serverPORT: str,
    maxMemSize: str,
    cpuCoreIDs: str,
    nodeType: str = "master",
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
            <p>Please select a valid master node from the dropdown menu.</p>
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
    </body>
    </html>
    """
    return HTMLResponse(content=response_message)

@app.get("/maintain/view-master-nodes-dropdown", response_class=HTMLResponse)
async def view_master_nodes_dropdown():
    """
    Returns a list of master nodes as a dropdown menu for the "Add Node" form.
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
            return "<option value=''>No active master nodes found</option>"

        # Query the cluster for master nodes
        cmd_status, cmd_output = subprocess.getstatusoutput(
            redisConnectCmd(contact_node[0], contact_node[1], ' CLUSTER NODES | grep master'))

        if cmd_status != 0:
            return "<option value=''>Error retrieving master nodes</option>"

        lines = cmd_output.strip().split('\n')
        for line in lines:
            parts = line.split()
            if len(parts) >= 9 and "master" in line and "fail" not in line:
                node_id = parts[0]
                ip_port = parts[1]
                master_nodes.append((node_id, ip_port))

        # Generate HTML options for the dropdown
        options = "".join([f"<option value='{node[0]}'>{node[1]}</option>" for node in master_nodes])
        return options
    except Exception as e:
        return f"<option value=''>Error: {str(e)}</option>"

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
                    <div class="error-message">
                        <p style='color: red;'>Node ID {nodeId} doesn't exist. Valid range is 1-{len(pareNodes)}</p>
                    </div>
                    """)

                if not pareNodes[node_id_int - 1][4]:
                    return HTMLResponse(content=f"""
                    <div class="error-message">
                        <p style='color: red;'>Node {nodeId} is already marked as inactive</p>
                    </div>
                    """)

                # Get node details for display
                serverIP = pareNodes[node_id_int - 1][0][0]
                serverPORT = pareNodes[node_id_int - 1][1][0]

                # Show confirmation dialog with node details
                return HTMLResponse(content=f"""
                <div class="confirmation-needed">
                    <p>Are you sure you want to delete this node from the cluster?</p>
                    <p><strong>Node:</strong> {nodeId} - {serverIP}:{serverPORT}</p>
                    <p style='color: red;'>This operation cannot be undone!</p>
                    <div class="confirmation-buttons">
                        <button onclick="confirmDeleteNode('{nodeId}')" class="confirm-btn">Yes, Delete Node</button>
                        <button onclick="cancelDeleteNode()" class="cancel-btn">Cancel</button>
                    </div>
                </div>
                """)
            except Exception as e:
                return HTMLResponse(content=f"""
                <div class="error-message">
                    <p style='color: red;'>An error occurred while processing node {nodeId}: {str(e)}</p>
                </div>
                """)

        # If confirmed, delegate to the add_delete_node_wv function
        result_html = add_delete_node_wv('del', nodeId)

        # Return just the result HTML, not a full page
        return HTMLResponse(content=f"""
        <div class="delete-result">
            <h3>Delete Node Result</h3>
            <div>{result_html}</div>
        </div>
        """)
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return HTMLResponse(content=f"""
        <div class="error-message">
            <h3>Unexpected Error</h3>
            <p style='color: red;'>An unexpected error occurred: {str(e)}</p>
            <pre style='background-color: #f8f8f8; padding: 10px; overflow-x: auto; font-size: 12px;'>{trace}</pre>
        </div>
        """)

@app.get("/maintain/move-slots/", response_class=HTMLResponse)
async def move_slots():
    """
    Endpoint for moving slots between Redis nodes (not implemented yet).
    """
    return HTMLResponse(content="""
    <div style="background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin: 10px 0;">
        <h4>Feature Not Implemented</h4>
        <p>The Move Slots feature is not implemented yet. This will allow you to:</p>
        <ul>
            <li>Move specific slots between Redis master nodes</li>
            <li>Rebalance slots across the cluster</li>
            <li>Optimize data distribution</li>
        </ul>
        <p>This feature will be available in a future version.</p>
    </div>
    """)

@app.get("/maintain/version-upgrade/", response_class=HTMLResponse)
async def version_upgrade():
    """
    Endpoint for upgrading Redis node versions (not implemented yet).
    """
    return HTMLResponse(content="""
    <div style="background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin: 10px 0;">
        <h4>Feature Not Implemented</h4>
        <p>The Version Upgrade feature is not implemented yet. This will allow you to:</p>
        <ul>
            <li>Upgrade Redis nodes to newer versions</li>
            <li>Perform rolling upgrades with minimal downtime</li>
            <li>Verify compatibility across your cluster</li>
        </ul>
        <p>This feature will be available in a future version.</p>
    </div>
    """)

@app.get("/maintain/version-control/", response_class=HTMLResponse)
async def version_control():
    """
    Endpoint for Redis version control (not implemented yet).
    """
    return HTMLResponse(content="""
    <div style="background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin: 10px 0;">
        <h4>Feature Not Implemented</h4>
        <p>The Version Control feature is not implemented yet. This will allow you to:</p>
        <ul>
            <li>Check Redis versions across your cluster</li>
            <li>Ensure version consistency</li>
            <li>Manage version compatibility issues</li>
        </ul>
        <p>This feature will be available in a future version.</p>
    </div>
    """)

@app.get("/maintain/server-maintain/", response_class=HTMLResponse)
async def server_maintain():
    """
    Endpoint for server maintenance operations (not implemented yet).
    """
    return HTMLResponse(content="""
    <div style="background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin: 10px 0;">
        <h4>Feature Not Implemented</h4>
        <p>The Server Maintenance feature is not implemented yet. This will allow you to:</p>
        <ul>
            <li>Monitor server resources</li>
            <li>Perform server maintenance tasks</li>
            <li>Schedule and automate maintenance operations</li>
        </ul>
        <p>This feature will be available in a future version.</p>
    </div>
    """)

@app.get("/maintain/migrate-data/", response_class=HTMLResponse)
async def migrate_data():
    """
    Endpoint for migrating data from remote Redis (not implemented yet).
    """
    return HTMLResponse(content="""
    <div style="background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin: 10px 0;">
        <h4>Feature Not Implemented</h4>
        <p>The Migrate Data feature is not implemented yet. This will allow you to:</p>
        <ul>
            <li>Import data from external Redis instances</li>
            <li>Migrate between Redis deployment types</li>
            <li>Perform incremental data migration</li>
        </ul>
        <p>This feature will be available in a future version.</p>
    </div>
    """)

@app.get("/maintain/slot-balancer/", response_class=HTMLResponse)
async def slot_balancer():
    """
    Endpoint for cluster slot balancing (not implemented yet).
    """
    return HTMLResponse(content="""
    <div style="background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin: 10px 0;">
        <h4>Feature Not Implemented</h4>
        <p>The Slot Balancer feature is not implemented yet. This will allow you to:</p>
        <ul>
            <li>Automatically balance slots across Redis masters</li>
            <li>Optimize for memory usage or CPU load</li>
            <li>Schedule rebalancing operations</li>
        </ul>
        <p>This feature will be available in a future version.</p>
    </div>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=(pareServerIp), port=(pareWebPort))
