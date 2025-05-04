# !/usr/bin/python
#paredicma webview v1.0
#date: 27.02.2024
#author: alperyz

import os
import subprocess
import traceback

from pareNodeList import *
from pareConfig import *
from pareFunc import *

import socket
from subprocess import getstatusoutput
from time import sleep
import sys


def nodeInfo_wv(redisNode, cmd):
    nodeIP, nodePort = redisNode.split(':')
    retVal = 'Unknown'

    if pingServer(nodeIP):
        listStatus, listResponse = subprocess.getstatusoutput(redisConnectCmd(nodeIP, nodePort, 'info ' + cmd))
        if listStatus == 0:
            response_lines = listResponse.split('\n')
            html_response = "<br>".join(response_lines)  # Convert each line to HTML format
            retVal = html_response
        else:
            retVal = f"<span style='color: red;'>!!! No Information or Connection Problem !!!</span>"
    else:
        retVal = f"<span style='color: orange;'>!!! Server Unreachable !!!</span>"

    return retVal


def serverInfo_wv(serverIP):
    # Ping the server to check if it's reachable
    if pingServer(serverIP):
        try:
            server_name = socket.gethostbyaddr(serverIP)[0]
        except socket.herror:
            server_name = "Unknown"  # Handle the case where hostname lookup fails

        # Check SSH availability
        if is_ssh_available(serverIP):
            html_content = f"""
            <h2>Server Information ({serverIP} - {server_name})</h2>
            <h3>CPU Cores</h3>
            <pre>{getcmdOutput_wv(serverIP, "numactl --hardware")}</pre>
            <h3>Memory Usage</h3>
            <pre>{getcmdOutput_wv(serverIP, "free -g")}</pre>
            <h3>Disk Usage</h3>
            <pre>{getcmdOutput_wv(serverIP, "df -h")}</pre>
            <h3>Redis Nodes</h3>
            {getredisnodeInfo_wv(serverIP)}
            """
        else:
            html_content = f"<p> {serverIP} SSH connection not working!</p>"
    else:
        html_content = f"<p> Server: {serverIP} Unreachable !!!!</p>"

    return html_content


def getcmdOutput_wv(serverIP, command):
        if serverIP == pareServerIp:
            status, output = subprocess.getstatusoutput(command)
        else:
            ssh_command = f'ssh -q -o "StrictHostKeyChecking no" {pareOSUser}@{serverIP} -C "{command}"'
            status, output = subprocess.getstatusoutput(ssh_command)
        return output if status == 0 else f"Error executing command: {command}"


def getredisnodeInfo_wv(serverIP):
    redisnodeInfo = ""
    nodenumbers = getnodeNumbers(serverIP)

    for pareNode in pareNodes:
        if pareNode[0][0] == serverIP:
            portNumber = pareNode[1][0]
            if pareNode[4]:
                if pingServer(serverIP):
                    returnVal = slaveORMasterNode(serverIP, portNumber)
                    nodenumber = nodenumbers.pop(0)
                    if returnVal == 'M':
                        redisnodeInfo += f"<p style='color: green;'> Server IP: {serverIP} | Node Number: {nodenumber} | Port: {portNumber} | Status: UP</p>"
                    elif returnVal == 'S':
                        redisnodeInfo += f"<p style='color: #001f3f;'> Server IP: {serverIP} | Node Number: {nodenumber} | Port: {portNumber} | Status: UP</p>"
                    else:
                        redisnodeInfo += f"<p style='color: red;'> Server IP: {serverIP} | Node Number: {nodenumber} | Port: {portNumber} | Status: DOWN</p>"
                else:
                    redisnodeInfo += f"<p style='color: orange;'> Server IP: {serverIP} | Node Number: {nodenumbers.pop(0)} | Port: {portNumber} | Status: Unknown</p>"
    return redisnodeInfo


def slotInfo_wv(nodeIP, portNumber):
    try:
        html_content = f"""
        <h2 class="section-title">Cluster Information from RedisNode: {nodeIP}:{portNumber}</h2>
        """
        
        # Collect master nodes information and slot information
        try:
            master_nodes_output = subprocess.check_output(
                redisConnectCmd(nodeIP, portNumber, ' CLUSTER NODES | grep master'),
                shell=True).decode()

            # Get cluster check information for slots, keys and replicas
            clusterString = f"{redisBinaryDir}src/redis-cli --cluster check {nodeIP}:{portNumber}"
            if redisPwdAuthentication == 'on':
                clusterString += f" -a {redisPwd}"

            check_output = subprocess.check_output(clusterString, shell=True).decode()

            # Extract the summary information from the check output
            node_stats = {}  # Dictionary to store node stats keyed by node ID

            # Parse the cluster check output for stats
            for line in check_output.split('\n'):
                if '->' in line:
                    parts = line.split('->')
                    if len(parts) >= 2:
                        endpoint_part = parts[0].strip()
                        stats_part = parts[1].strip()

                        # Extract node ID (short form)
                        node_id_short = endpoint_part.split('(')[1].split('...')[0] if '(' in endpoint_part else ""

                        # Extract stats
                        keys = stats_part.split('|')[0].strip()
                        slots = stats_part.split('|')[1].strip()
                        slaves = stats_part.split('|')[2].strip() if len(stats_part.split('|')) > 2 else ""

                        # Store in dictionary with short node ID as key
                        node_stats[node_id_short] = {
                            'keys': keys,
                            'slots': slots,
                            'slaves': slaves
                        }

            # Now create the consolidated table
            html_content += """
            <h3 class="section-title">Summary of Cluster</h3>
            <table class="cluster-info-table">
                <thead>
                    <tr>
                        <th>Node ID</th>
                        <th>Endpoint</th>
                        <th>Slot Range</th>
                        <th>Slots</th>
                        <th>Keys</th>
                        <th>Replicas</th>
                    </tr>
                </thead>
                <tbody>
            """

            # Process and merge information from both sources
            for line in master_nodes_output.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 8:
                    node_id = parts[0]
                    endpoint = parts[1].split('@')[0]
                    slot_range = ' '.join([part for part in parts[8:] if '-' in part or part.isdigit()])

                    # Get stats from the node_stats dictionary using the node_id prefix
                    node_id_short = node_id[:8]  # Using first 8 chars as the shortened ID
                    stats = node_stats.get(node_id_short, {'keys': 'N/A', 'slots': 'N/A', 'slaves': 'N/A'})

                    html_content += f"""
                    <tr>
                        <td><span class="node-id master-node">{node_id}</span></td>
                        <td>{endpoint}</td>
                        <td>{slot_range}</td>
                        <td>{stats['slots']}</td>
                        <td>{stats['keys']}</td>
                        <td>{stats['slaves']}</td>
                    </tr>
                    """

            html_content += """
                </tbody>
            </table>
            """
            
            # Format the status lines
            status_lines = []
            for line in check_output.split('\n'):
                if '[OK]' in line:
                    status_lines.append(line)

            if status_lines:
                html_content += "<div class='cluster-check'>"
                for line in status_lines:
                    html_content += f'<div class="status-ok">{line}</div>'
                html_content += "</div>"

            # Format the detailed information - keep the detailed node information section
            html_content += """
            <h3 class="section-title">Detailed Cluster Status</h3>
            <div class="cluster-check">
            """
            
            # Extract detailed node information from the check output
            detailed_info = []
            in_detail_section = False

            for line in check_output.split('\n'):
                if line.startswith('>>>'):
                    in_detail_section = True
                detailed_info.append(line) if in_detail_section else None

            # Master and slave tables
            master_nodes = []
            slave_nodes = []
            
            current_node = {}
            for i, line in enumerate(detailed_info):
                if line.startswith('M:') or line.startswith('S:'):
                    if current_node:  # Save previous node if any
                        if current_node['type'] == 'M':
                            master_nodes.append(current_node)
                        else:
                            slave_nodes.append(current_node)
                    
                    # Start new node
                    node_type = 'M' if line.startswith('M:') else 'S'
                    parts = line.strip()[2:].split()
                    if len(parts) >= 2:
                        node_id = parts[0]
                        endpoint = parts[1]
                        current_node = {'type': node_type, 'id': node_id, 'endpoint': endpoint, 'slots': '', 'replicas': '', 'replicates': ''}
                
                elif 'slots:' in line and current_node:
                    slots_info = line.strip()
                    current_node['slots'] = slots_info
                
                elif 'replica' in line and current_node:
                    replicas_info = line.strip()
                    current_node['replicas'] = replicas_info
                
                elif 'replicates' in line and current_node:
                    replicates_info = line.strip()
                    current_node['replicates'] = replicates_info
            
            # Add the last node
            if current_node:
                if current_node['type'] == 'M':
                    master_nodes.append(current_node)
                else:
                    slave_nodes.append(current_node)
            
            # Format master nodes
            html_content += """
            <h4>Master Nodes</h4>
            <table class="cluster-info-table">
                <thead>
                    <tr>
                        <th>Node ID</th>
                        <th>Endpoint</th>
                        <th>Slots</th>
                        <th>Replicas</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for node in master_nodes:
                slots_display = node['slots'].replace('slots:', '').strip()
                replicas_display = node['replicas'].strip()
                
                html_content += f"""
                <tr>
                    <td><span class="node-id master-node">{node['id']}</span></td>
                    <td>{node['endpoint']}</td>
                    <td>{slots_display}</td>
                    <td>{replicas_display}</td>
                </tr>
                """
            
            html_content += """
                </tbody>
            </table>
            """
            
            # Format slave nodes
            html_content += """
            <h4>Replica Nodes</h4>
            <table class="cluster-info-table">
                <thead>
                    <tr>
                        <th>Node ID</th>
                        <th>Endpoint</th>
                        <th>Slots</th>
                        <th>Replicates</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for node in slave_nodes:
                slots_display = node['slots'].replace('slots:', '').strip()
                replicates_display = node['replicates'].replace('replicates', '').strip()
                
                html_content += f"""
                <tr>
                    <td><span class="node-id slave-node">{node['id']}</span></td>
                    <td>{node['endpoint']}</td>
                    <td>{slots_display}</td>
                    <td><span class="node-id">{replicates_display}</span></td>
                </tr>
                """
            
            html_content += """
                </tbody>
            </table>
            """
            
            # Format the closing checks and status
            status_sections = []
            current_section = []
            
            for line in detailed_info:
                if line.startswith('[OK]') or line.startswith('[ERR]'):
                    if current_section:
                        status_sections.append('\n'.join(current_section))
                        current_section = []
                    status_sections.append(line)
                elif line.startswith('>>>'):
                    if current_section:
                        status_sections.append('\n'.join(current_section))
                    current_section = [line]
                else:
                    current_section.append(line)
            
            if current_section:
                status_sections.append('\n'.join(current_section))
            
            for section in status_sections:
                if '[OK]' in section:
                    html_content += f'<div class="status-ok">{section}</div>'
                elif '>>>' in section:
                    html_content += f'<div>{section}</div>'
                else:
                    html_content += f'<div>{section}</div>'
            
            html_content += """
            </div>
            """
            
        except subprocess.CalledProcessError as e:
            html_content += f"<p style='color: red;'>Error retrieving cluster status: {str(e)}</p>"
        
        return html_content
        
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return f"""
        <div class="error-message">
            <h3>Error Retrieving Cluster Information</h3>
            <p>An error occurred: {str(e)}</p>
            <pre>{trace}</pre>
        </div>
        """


def clusterStateInfo_wv(nodeIP, portNumber):
    # Check server availability before attempting to execute the command
    if pingServer(nodeIP):
        try:
            # Execute the command to retrieve cluster information
            cluster_info = subprocess.check_output(
                redisConnectCmd(nodeIP, portNumber, ' CLUSTER INFO | grep cluster_state'), shell=True).decode()

        except subprocess.CalledProcessError as e:
            # Handle errors gracefully
            cluster_info = f"<p>Error retrieving cluster information for Node IP: {nodeIP}, Port: {portNumber}</p>"
    else:
        cluster_info = f"<p>Server Unreachable!: {nodeIP}</p>"

    return cluster_info


def check_if_master(nodeIP, portNumber):
    """
    Check if the node is a master node and if it has slaves
    Returns: (is_master, has_slave)
    """
    is_master = False
    has_slave = False

    try:
        # Use slaveORMasterNode directly for consistent role identification across code
        is_master = slaveORMasterNode(nodeIP, portNumber) == 'M'

        if is_master:
            # Check if it has slaves
            pingStatus, pingResponse = subprocess.getstatusoutput(
                redisConnectCmd(nodeIP, portNumber, ' info replication | grep connected_slaves '))
            if pingStatus == 0 and pingResponse.find(':0') == -1:
                has_slave = True
    except Exception as e:
        print(f"Error checking master status: {e}")

    return (is_master, has_slave)


def reload_pare_nodes():
    """
    Reloads the pareNodes configuration from the pareNodeList.py file.
    This allows updating the node list without restarting the application.
    """
    global pareNodes
    try:
        # Reload the pareNodeList module to get the updated configuration
        import importlib
        importlib.reload(sys.modules['pareNodeList'])
        from pareNodeList import pareNodes as fresh_pareNodes

        # Update the global pareNodes variable
        globals()['pareNodes'] = fresh_pareNodes
        pareNodes = fresh_pareNodes

        return True, f"Node configuration reloaded successfully. {len([node for node in pareNodes if node[4]])} active nodes."
    except Exception as e:
        return False, f"Error reloading node configuration: {str(e)}"


def node_action_wv(redisNode, action, confirmed=False):
    """
    Performs start, stop, or restart action on a given Redis node via web request.
    If stopping a master node, asks for confirmation unless confirmed=True is passed.
    """
    # Declare logWrite as global at the beginning of the function
    global logWrite

    try:
        nodeIP, portNumber = redisNode.split(':')
        node_details = None
        node_index = -1

        # Find the node details in pareNodes
        for i, node in enumerate(pareNodes):
            if node[0][0] == nodeIP and node[1][0] == portNumber and node[4]:  # Check if active
                node_details = node
                node_index = i + 1  # Node number is index + 1
                break

        if not node_details:
            return f"<p style='color: red;'>Error: Node {redisNode} not found or is inactive in configuration.</p>"

        dedicateCpuCores = node_details[2][0]
        node_num_str = str(node_index)

        # Check if the node is already running when trying to start it
        if action.lower() == 'start':
            if pingredisNode(nodeIP, portNumber):
                return f"""
                <div class="response-container">
                    <p style='color: orange;'><strong>Notice:</strong> Node {redisNode} is already running.</p>
                    <p>No action was taken as the node is already in the desired state.</p>
                </div>
                """

        # For stop or restart action, check if the node is master and if confirmation is required
        if action.lower() == 'stop' or action.lower() == 'restart':
            is_master, has_slave = check_if_master(nodeIP, portNumber)

            if is_master and not confirmed:
                # Return a special message that requires confirmation
                if has_slave:
                    return f"""
                    <div class="confirmation-needed" id="confirmation-dialog">
                        <p style='color: red; font-weight: bold;'>Warning: This node ({redisNode}) is a MASTER node with slaves!</p>
                        <p>{"Stopping" if action.lower() == 'stop' else "Restarting"} this node will trigger master/slave failover.</p>
                        <p>Do you want to continue?</p>
                        <button class="confirm-btn" data-node="{redisNode}" data-action="{action.lower()}">Yes, {action.capitalize()} the Node</button>
                        <button class="cancel-btn">Cancel</button>
                    </div>
                    """
                else:
                    return f"""
                    <div class="confirmation-needed" id="confirmation-dialog">
                        <p style='color: red; font-weight: bold;'>Warning: This node ({redisNode}) is a MASTER node with NO slaves!</p>
                        <p style='color: red;'>{"Stopping" if action.lower() == 'stop' else "Restarting"} this node will cause Redis cluster to FAIL!</p>
                        <p>Do you want to continue?</p>
                        <button class="confirm-btn" data-node="{redisNode}" data-action="{action.lower()}">Yes, {action.capitalize()} the Node</button>
                        <button class="cancel-btn">Cancel</button>
                    </div>
                    """

        # Check if trying to stop a node that's already stopped
        if action.lower() == 'stop' and not pingredisNode(nodeIP, portNumber):
            return f"""
            <div class="response-container">
                <p style='color: orange;'><strong>Notice:</strong> Node {redisNode} is already stopped.</p>
                <p>No action was taken as the node is already in the desired state.</p>
            </div>
            """

        action_func = None
        action_gerund = ""  # For user feedback

        if action.lower() == 'start':
            action_func = startNode
            action_gerund = "starting"
        elif action.lower() == 'stop':
            action_func = stopNode
            action_gerund = "stopping"
        elif action.lower() == 'restart':
            action_func = restartNode
            action_gerund = "restarting"
        else:
            return f"<p style='color: red;'>Error: Invalid action '{action}'. Allowed actions are start, stop, restart.</p>"

        log_messages = []
        original_logWrite = logWrite  # Store original logWrite function

        # Temporarily redirect logWrite to capture messages
        def capture_log(*args):
            log_text_str = str(args[1]) if len(args) > 1 else ""
            log_messages.append(log_text_str)  # args[1] is the logText
            original_logWrite(*args)  # Call original logWrite as well

        # Replace the global logWrite function temporarily
        logWrite = capture_log

        try:
            # For stop and restart actions with confirmation, handle it differently
            if (action.lower() == 'stop' or action.lower() == 'restart') and confirmed:
                # First check if node is master and has slaves
                is_master, has_slave = check_if_master(nodeIP, portNumber)
                if is_master and has_slave:
                    log_messages.append(f"Master/slave switch process is starting for {nodeIP}:{portNumber}... This might take some time, be patient!")
                    # Perform master/slave failover before stopping
                    switchMasterSlave(nodeIP, node_index, portNumber)

                # Now perform the action
                if action.lower() == 'stop':
                    log_messages.append(f"Stopping Redis node {nodeIP}:{portNumber}")
                    stopNode(nodeIP, node_num_str, portNumber, non_interactive=True)
                elif action.lower() == 'restart':
                    log_messages.append(f"Restarting Redis node {nodeIP}:{portNumber}")
                    # Call stopNode with non_interactive flag first, then startNode
                    stopNode(nodeIP, node_num_str, portNumber, non_interactive=True)
                    startNode(nodeIP, node_num_str, portNumber, dedicateCpuCores)
            else:
                # Normal action execution for non-stop actions or non-master nodes
                if action.lower() in ['start', 'restart']:
                    action_func(nodeIP, node_num_str, portNumber, dedicateCpuCores)
                else:  # stopNode only needs nodeIP, node_num_str, portNumber
                    action_func(nodeIP, node_num_str, portNumber)

            # Restore original logWrite
            logWrite = original_logWrite

            # Check ping status after action
            sleep(5)  # Give node time to start/stop
            final_ping_status = pingredisNode(nodeIP, portNumber)

            result_message = f"Action '{action}' completed for node {redisNode}."
            # Create the status span separately
            status_span = ""
            if action.lower() == 'start' or action.lower() == 'restart':
                status_span = "<span style='color: green;'>Running</span>" if final_ping_status else "<span style='color: red;'>Not Running</span>"
            elif action.lower() == 'stop':
                status_span = "<span style='color: gray;'>Stopped</span>" if not final_ping_status else "<span style='color: red;'>Still Running?</span>"

            # Add the status span to the result message
            if status_span:
                result_message += f" Final status: {status_span}."

            # Format captured logs
            log_output = "<br>".join(log_messages).replace('\n', '<br>')  # Ensure newlines are breaks

            return f"""
                <p>{result_message}</p>
                <h4>Logs:</h4>
                <pre style='padding: 10px; border: 1px solid #ccc;'>{log_output if log_output else "No specific log output captured."}</pre>
                """

        except Exception as e:
            # Restore original logWrite in case of error
            logWrite = original_logWrite
            # Format captured logs even in case of error
            log_output_error = "<br>".join(log_messages).replace('\n', '<br>')
            return f"<p style='color: red;'>Error {action_gerund} node {redisNode}: {e}</p><pre>{log_output_error}</pre>"

    except Exception as e:
        return f"<p style='color: red;'>An unexpected error occurred: {e}</p>"


def switch_master_slave_wv(redisNode):
    """
    Switches roles between a master node and one of its slaves via web request.
    The node specified should be a master node with at least one slave.
    """
    global logWrite

    try:
        nodeIP, portNumber = redisNode.split(':')
        node_details = None
        node_index = -1

        # Find the node details in pareNodes
        for i, node in enumerate(pareNodes):
            if node[0][0] == nodeIP and node[1][0] == portNumber and node[4]:  # Check if active
                node_details = node
                node_index = i + 1  # Node number is index + 1
                break

        if not node_details:
            return f"<p style='color: red;'>Error: Node {redisNode} not found or is inactive in configuration.</p>"

        # Check if the node is a master
        is_master = slaveORMasterNode(nodeIP, portNumber) == 'M'
        if not is_master:
            return f"<p style='color: red;'>Error: Node {redisNode} is not a master node. Only master nodes can be switched with slaves.</p>"

        # Check if the master has slaves
        has_slave = False
        slave_info = None

        processStatus, processResponse = subprocess.getstatusoutput(
            redisConnectCmd(nodeIP, portNumber, ' info replication | grep slave0'))

        if processStatus == 0 and processResponse and 'online' in processResponse:
            has_slave = True
            slave_info = processResponse
        else:
            return f"<p style='color: red;'>Error: Master node {redisNode} has no slaves available for failover. Cannot perform master/slave switch.</p>"

        if not has_slave:
            return f"<p style='color: red;'>Error: Master node {redisNode} has no slaves. Cannot perform master/slave switch.</p>"

        # Extract slave information for display
        cutCursor1 = slave_info.find('ip=')
        temp_response = slave_info[cutCursor1 + 3:]
        cutCursor2 = temp_response.find(',')
        slaveIP = temp_response[:cutCursor2]

        temp_response = temp_response[cutCursor2:]
        cutCursor3 = temp_response.find('port=')
        temp_response = temp_response[cutCursor3 + 5:]
        cutCursor4 = temp_response.find(',')
        slavePort = temp_response[:cutCursor4]

        # Capture log messages
        log_messages = []
        original_logWrite = logWrite  # Store original logWrite function

        # Temporarily redirect logWrite to capture messages
        def capture_log(*args):
            log_text_str = str(args[1]) if len(args) > 1 else ""
            log_messages.append(log_text_str)  # args[1] is the logText
            original_logWrite(*args)  # Call original logWrite as well

        # Replace the global logWrite function temporarily
        logWrite = capture_log

        try:
            # Perform the master/slave switch
            log_messages.append(f"Beginning master/slave switch for {redisNode}...")
            log_messages.append(f"Master/slave switch process is starting... This might take some time, be patient!")

            # Call the existing switchMasterSlave function
            success = switchMasterSlave(nodeIP, node_index, portNumber)

            # Restore original logWrite
            logWrite = original_logWrite

            # Check the new status after switch
            sleep(5)  # Give some time for the switch to complete
            new_master_role = slaveORMasterNode(slaveIP, slavePort)
            new_slave_role = slaveORMasterNode(nodeIP, portNumber)

            switch_successful = new_master_role == 'M' and new_slave_role == 'S'

            if switch_successful:
                # Format captured logs
                log_output = "<br>".join(log_messages).replace('\n', '<br>')

                return f"""
                <div style="margin-bottom: 20px;">
                    <p style='color: green; font-weight: bold;'>Master/slave switch completed successfully!</p>
                    <ul>
                        <li>Previous Master: {nodeIP}:{portNumber} (now Slave)</li>
                        <li>New Master: {slaveIP}:{slavePort}</li>
                    </ul>
                    <h4>Logs:</h4>
                    <pre style='padding: 10px; border: 1px solid #ccc;'>{log_output}</pre>
                </div>
                """
            else:
                log_output = "<br>".join(log_messages).replace('\n', '<br>')
                return f"""
                <p style='color: red; font-weight: bold;'>Failed to switch master/slave roles.</p>
                <p>Current roles: {nodeIP}:{portNumber} is {new_slave_role}, {slaveIP}:{slavePort} is {new_master_role}</p>
                <h4>Logs:</h4>
                <pre style='padding: 10px; border: 1px solid #ccc;'>{log_output}</pre>
                """

        except Exception as e:
            # Restore original logWrite in case of error
            logWrite = original_logWrite
            # Format captured logs even in case of error
            log_output_error = "<br>".join(log_messages).replace('\n', '<br>')
            return f"<p style='color: red;'>Error during master/slave switch: {e}</p><pre>{log_output_error}</pre>"

    except Exception as e:
        return f"<p style='color: red;'>An unexpected error occurred: {str(e)}</p>"


def change_config_wv(redisNode, parameter, value, persist=False):
    """
    Changes a Redis configuration parameter for a given node.

    Args:
        redisNode: The Redis node in format IP:Port
        parameter: The Redis configuration parameter to change
        value: The new value for the parameter
        persist: If True, persist the changes to redis.conf file

    Returns:
        HTML-formatted result of the operation
    """
    try:
        nodeIP, portNumber = redisNode.split(':')
        node_details = None
        node_index = -1

        # Find the node details in pareNodes
        for i, node in enumerate(pareNodes):
            if node[0][0] == nodeIP and node[1][0] == portNumber and node[4]:  # Check if active
                node_details = node
                node_index = i + 1  # Node number is index + 1
                break

        if not node_details:
            return f"<p style='color: red;'>Error: Node {redisNode} not found or is inactive in configuration.</p>"

        # Validation for parameter and value
        if not parameter or not value:
            return f"<p style='color: red;'>Error: Parameter and value must be specified.</p>"

        # Check if node is reachable
        if not pingredisNode(nodeIP, portNumber):
            return f"<p style='color: red;'>Error: Cannot connect to node {redisNode}.</p>"

        # Execute the CONFIG SET command
        cmd_status, cmd_response = subprocess.getstatusoutput(
            redisConnectCmd(nodeIP, portNumber, f' CONFIG SET {parameter} "{value}"'))

        if cmd_status != 0 or 'OK' not in cmd_response:
            return f"""
            <div>
                <p style='color: red;'>Failed to set configuration parameter '{parameter}' to '{value}'</p>
                <p>Response: {cmd_response}</p>
            </div>
            """

        # If persist is True, save the configuration to the config file
        conf_saved = False
        if persist:
            # Send CONFIG REWRITE command to make the change persistent
            rewrite_status, rewrite_response = subprocess.getstatusoutput(
                redisConnectCmd(nodeIP, portNumber, ' CONFIG REWRITE'))

            conf_saved = (rewrite_status == 0 and 'OK' in rewrite_response)

        # Get current value to confirm the change
        get_status, get_response = subprocess.getstatusoutput(
            redisConnectCmd(nodeIP, portNumber, f' CONFIG GET {parameter}'))

        if get_status == 0 and parameter in get_response:
            current_value = get_response.split('\n')[1] if '\n' in get_response else get_response.split(' ')[1]

            result = f"""
            <div>
                <p style='color: green;'>Successfully changed configuration parameter</p>
                <ul>
                    <li><strong>Node:</strong> {redisNode}</li>
                    <li><strong>Parameter:</strong> {parameter}</li>
                    <li><strong>New Value:</strong> {current_value}</li>
                    <li><strong>Persisted to config file:</strong> {'Yes' if conf_saved else 'No'}</li>
                </ul>
                <p><strong>Note:</strong> Some configuration parameters require a restart to take effect.</p>
            </div>
            """
        else:
            result = f"""
            <div>
                <p style='color: orange;'>Configuration changed but couldn't verify current value.</p>
                <ul>
                    <li><strong>Node:</strong> {redisNode}</li>
                    <li><strong>Parameter:</strong> {parameter}</li>
                    <li><strong>Set Value:</strong> {value}</li>
                    <li><strong>Persisted to config file:</strong> {'Yes' if conf_saved else 'No'}</li>
                </ul>
            </div>
            """

        return result

    except Exception as e:
        return f"<p style='color: red;'>An unexpected error occurred: {str(e)}</p>"


def get_config_wv(redisNode, parameter="*"):
    """
    Gets Redis configuration parameters for a given node.

    Args:
        redisNode: The Redis node in format IP:Port
        parameter: The Redis configuration parameter to get, defaults to "*" for all parameters

    Returns:
        HTML-formatted display of current configuration
    """
    try:
        nodeIP, portNumber = redisNode.split(':')

        # Check if node is reachable
        if not pingredisNode(nodeIP, portNumber):
            return f"<p style='color: red;'>Error: Cannot connect to node {redisNode}.</p>"

        # Execute the CONFIG GET command
        cmd_status, cmd_response = subprocess.getstatusoutput(
            redisConnectCmd(nodeIP, portNumber, f' CONFIG GET {parameter}'))

        if cmd_status != 0:
            return f"""
            <div>
                <p style='color: red;'>Failed to get configuration parameter(s)</p>
                <p>Response: {cmd_response}</p>
            </div>
            """

        # Parse the response into key-value pairs
        lines = cmd_response.strip().split('\n')
        config_items = []

        # Redis returns config in alternating key-value format
        for i in range(0, len(lines), 2):
            if i + 1 < len(lines):
                config_items.append((lines[i], lines[i+1]))

        # Format the configuration items as an HTML table
        result = f"""
        <div>
            <h3>Configuration for {redisNode}</h3>
            <table class="config-table" border="1">
                <thead>
                    <tr>
                        <th>Parameter</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f"<tr><td>{item[0]}</td><td>{item[1]}</td></tr>" for item in config_items])}
                </tbody>
            </table>
        </div>
        """

        return result

    except Exception as e:
        return f"<p style='color: red;'>An unexpected error occurred: {str(e)}</p>"


def save_config_wv(redisNode):
    """
    Saves Redis configuration to redis.conf file for a given node or all nodes.

    Args:
        redisNode: The Redis node in format IP:Port or "all" for all nodes

    Returns:
        HTML-formatted result of the operation
    """
    results = []

    try:
        if redisNode == "all":
            # For all nodes, iterate through active nodes
            for node in pareNodes:
                if node[4]:  # Check if node is active
                    nodeIP = node[0][0]
                    portNumber = node[1][0]
                    results.append(save_single_node_config(nodeIP, portNumber))
        else:
            # For single node
            nodeIP, portNumber = redisNode.split(':')
            results.append(save_single_node_config(nodeIP, portNumber))

        # Format results in HTML
        result_html = "<div class='results'>"
        success_count = sum(1 for result in results if "success" in result.lower())
        error_count = len(results) - success_count

        result_html += f"<p>Summary: {success_count} successful, {error_count} failed</p>"

        for result in results:
            result_html += f"<div class='result-item'>{result}</div>"

        result_html += "</div>"
        return result_html

    except Exception as e:
        return f"<p style='color: red;'>An unexpected error occurred: {str(e)}</p>"

def save_single_node_config(nodeIP, portNumber):
    """
    Helper function to save configuration for a single node.
    """
    try:
        # Check if node is reachable
        if not pingredisNode(nodeIP, portNumber):
            return f"<p style='color: red;'>Error: Cannot connect to node {nodeIP}:{portNumber}.</p>"

        # Execute the CONFIG REWRITE command
        cmd_status, cmd_response = subprocess.getstatusoutput(
            redisConnectCmd(nodeIP, portNumber, ' CONFIG REWRITE'))

        if cmd_status == 0 and 'OK' in cmd_response:
            return f"<p style='color: green;'>Successfully saved configuration for {nodeIP}:{portNumber} to redis.conf</p>"
        else:
            return f"<p style='color: red;'>Failed to save configuration for {nodeIP}:{portNumber}: {cmd_response}</p>"

    except Exception as e:
        return f"<p style='color: red;'>Error saving configuration for {nodeIP}:{portNumber}: {str(e)}</p>"


def rolling_restart_wv(wait_minutes=0, restart_masters=True):
    """
    Performs a rolling restart of Redis cluster nodes, first slaves then masters.

    Args:
        wait_minutes: Wait time in minutes between node restarts
        restart_masters: Whether to restart master nodes after slaves

    Returns:
        HTML-formatted result of the operation
    """
    results = []
    restarted_nodes = []
    wait_seconds = int(wait_minutes) * 60

    try:
        # First restart all slave nodes
        results.append("<h3>Restarting Slave Nodes</h3>")
        for node_index, pareNode in enumerate(pareNodes, start=1):
            nodeIP = pareNode[0][0]
            portNumber = pareNode[1][0]
            dedicateCpuCores = pareNode[2][0]

            if pareNode[4]:  # Check if node is active
                # Check if node is reachable
                if pingredisNode(nodeIP, portNumber):
                    # Is this a slave node?
                    if slaveORMasterNode(nodeIP, portNumber) == 'S':
                        # Perform restart
                        results.append(f"<p>Restarting slave node {nodeIP}:{portNumber} (Node #{node_index})...</p>")

                        try:
                            # Store original logWrite function
                            original_logWrite = logWrite

                            # Temporarily redirect logWrite
                            log_messages = []
                            def capture_log(*args):
                                if len(args) > 1:
                                    log_text = str(args[1])
                                    log_messages.append(log_text)

                            # Replace logWrite temporarily
                            globals()['logWrite'] = capture_log

                            # Perform restart
                            restartNode(nodeIP, str(node_index), portNumber, dedicateCpuCores)

                            # Restore original logWrite
                            globals()['logWrite'] = original_logWrite

                            # Add node to restarted list
                            restarted_nodes.append(f"Node#{node_index} ({nodeIP}:{portNumber})")

                            # Format log messages
                            log_output = "<br>".join([msg for msg in log_messages if msg])
                            results.append(f"<div style='margin-left: 20px; padding: 10px;'>{log_output}</div>")

                            # Add status check
                            if pingredisNode(nodeIP, portNumber):
                                results.append(f"<p style='color: green;'>Node {nodeIP}:{portNumber} restarted successfully.</p>")
                            else:
                                results.append(f"<p style='color: red;'>Node {nodeIP}:{portNumber} failed to restart!</p>")

                            # Wait between restarts if specified
                            if wait_seconds > 0 and node_index < len(pareNodes):
                                results.append(f"<p>Waiting {wait_minutes} minute(s) before next restart...</p>")

                        except Exception as e:
                            # Restore original logWrite in case of error
                            globals()['logWrite'] = original_logWrite
                            results.append(f"<p style='color: red;'>Error restarting node {nodeIP}:{portNumber}: {str(e)}</p>")

        # Then restart master nodes if requested
        if restart_masters:
            results.append("<h3>Restarting Master Nodes</h3>")
            for node_index, pareNode in enumerate(pareNodes, start=1):
                nodeIP = pareNode[0][0]
                portNumber = pareNode[1][0]
                dedicateCpuCores = pareNode[2][0]

                if pareNode[4]:  # Check if node is active
                    # Check if node is reachable
                    if pingredisNode(nodeIP, portNumber):
                        # Is this a master node?
                        if slaveORMasterNode(nodeIP, portNumber) == 'M':
                            # Check if we've already restarted this node (might have been promoted from slave)
                            node_key = f"Node#{node_index} ({nodeIP}:{portNumber})"
                            if node_key in restarted_nodes:
                                results.append(f"<p>Skipping master node {nodeIP}:{portNumber} (Node #{node_index}) - already restarted.</p>")
                                continue

                            # Perform restart
                            results.append(f"<p>Restarting master node {nodeIP}:{portNumber} (Node #{node_index})...</p>")

                            try:
                                # Store original logWrite function
                                original_logWrite = logWrite

                                # Temporarily redirect logWrite
                                log_messages = []
                                def capture_log(*args):
                                    if len(args) > 1:
                                        log_text = str(args[1])
                                        log_messages.append(log_text)

                                # Replace logWrite temporarily
                                globals()['logWrite'] = capture_log

                                # First check if the master has slaves
                                has_slaves = isNodeHasSlave(nodeIP, node_index, portNumber)
                                if has_slaves:
                                    results.append(f"<p>Master node has slaves - will attempt failover before restart.</p>")
                                    # Trigger failover before restarting
                                    if switchMasterSlave(nodeIP, node_index, portNumber):
                                        results.append(f"<p style='color: green;'>Master/Slave failover successful.</p>")
                                    else:
                                        results.append(f"<p style='color: red;'>Master/Slave failover failed! Proceeding with restart.</p>")

                                # Perform restart
                                restartNode(nodeIP, str(node_index), portNumber, dedicateCpuCores)

                                # Restore original logWrite
                                globals()['logWrite'] = original_logWrite

                                # Format log messages
                                log_output = "<br>".join([msg for msg in log_messages if msg])
                                results.append(f"<div style='margin-left: 20px; padding: 10px;'>{log_output}</div>")

                                # Add status check
                                if pingredisNode(nodeIP, portNumber):
                                    results.append(f"<p style='color: green;'>Node {nodeIP}:{portNumber} restarted successfully.</p>")
                                else:
                                    results.append(f"<p style='color: red;'>Node {nodeIP}:{portNumber} failed to restart!</p>")

                                # Wait between restarts if specified
                                if wait_seconds > 0 and node_index < len(pareNodes):
                                    results.append(f"<p>Waiting {wait_minutes} minute(s) before next restart...</p>")

                            except Exception as e:
                                # Restore original logWrite in case of error
                                globals()['logWrite'] = original_logWrite
                                results.append(f"<p style='color: red;'>Error restarting node {nodeIP}:{portNumber}: {str(e)}</p>")

        # Check final cluster state
        results.append("<h3>Final Cluster State</h3>")
        # Find an active node to check cluster state
        for pareNode in pareNodes:
            nodeIP = pareNode[0][0]
            portNumber = pareNode[1][0]
            if pareNode[4] and pingredisNode(nodeIP, portNumber):
                cluster_state = clusterStateInfo_wv(nodeIP, portNumber)
                results.append(f"<p>Cluster state: {cluster_state}</p>")
                break

        return "".join(results)

    except Exception as e:
        return f"<p style='color: red;'>An unexpected error occurred: {str(e)}</p>"


def execute_command_wv(command, only_masters=False, wait_seconds=0):
    """
    Executes a Redis command on all nodes or only on master nodes.

    Args:
        command: The Redis command to execute
        only_masters: If True, execute only on master nodes
        wait_seconds: Wait time in seconds between node executions

    Returns:
        HTML-formatted result of the command execution
    """
    if not command:
        return "<p style='color: red;'>Error: No command specified.</p>"

    results = []
    node_count = 0
    success_count = 0

    try:
        results.append(f"<h3>Executing command: <code>{command}</code></h3>")

        for node_index, pareNode in enumerate(pareNodes, start=1):
            nodeIP = pareNode[0][0]
            portNumber = pareNode[1][0]

            if pareNode[4]:  # Check if node is active
                # Check if we should run on this node (masters only filter)
                if only_masters:
                    is_master = slaveORMasterNode(nodeIP, portNumber) == 'M'
                    if not is_master:
                        continue

                node_count += 1
                is_master = slaveORMasterNode(nodeIP, portNumber) == 'M'
                node_type = "Master" if is_master else "Slave"

                # Check if node is reachable
                if pingredisNode(nodeIP, portNumber):
                    try:
                        # Execute the command
                        cmd_status, cmd_output = subprocess.getstatusoutput(
                            redisConnectCmd(nodeIP, portNumber, command))

                        # Format output for display
                        output_lines = cmd_output.strip().split('\n')
                        formatted_output = "<br>".join(output_lines)

                        if cmd_status == 0:
                            success_count += 1
                            results.append(f"""
                            <div style='margin: 10px 0; padding: 10px; border-left: 4px solid green;'>
                                <h4>Node {nodeIP}:{portNumber} ({node_type}) - Success</h4>
                                <pre style='margin: 5px 0;'>{formatted_output}</pre>
                            </div>
                            """)
                        else:
                            results.append(f"""
                            <div style='margin: 10px 0; padding: 10px; border-left: 4px solid orange;'>
                                <h4>Node {nodeIP}:{portNumber} ({node_type}) - Command returned non-zero status</h4>
                                <pre style='margin: 5px 0;'>{formatted_output}</pre>
                            </div>
                            """)

                    except Exception as e:
                        results.append(f"""
                        <div style='margin: 10px 0; padding: 10px; border-left: 4px solid red;'>
                            <h4>Node {nodeIP}:{portNumber} ({node_type}) - Error</h4>
                            <p style='color: red;'>Error executing command: {str(e)}</p>
                        </div>
                        """)
                else:
                    results.append(f"""
                    <div style='margin: 10px 0; padding: 10px; border-left: 4px solid gray;'>
                        <h4>Node {nodeIP}:{portNumber} ({node_type}) - Not Reachable</h4>
                        <p>Could not connect to this node.</p>
                    </div>
                    """)

                # Wait between commands if specified
                if wait_seconds > 0 and node_index < len(pareNodes):
                    results.append(f"<p><em>Waiting {wait_seconds} seconds before next execution...</em></p>")
                    sleep(wait_seconds)

        # Add a summary
        filter_text = "master nodes" if only_masters else "nodes"
        results.append(f"<h3>Summary</h3>")
        results.append(f"<p>Command executed on {success_count} of {node_count} active {filter_text}.</p>")

        return "".join(results)

    except Exception as e:
        return f"<p style='color: red;'>An unexpected error occurred: {str(e)}</p>"


def show_redis_log_wv(redisNode, line_count=100):
    """
    Shows Redis log file content for a given node using CSS classes for styling.

    Args:
        redisNode: The Redis node in format IP:Port
        line_count: Number of lines to show from the end of the file

    Returns:
        HTML-formatted log content
    """
    try:
        # Validate line count
        try:
            line_count = int(line_count)
            if line_count <= 0:
                return "<p style='color: red;'>Error: Line count must be greater than 0.</p>"
            if line_count > 10000:
                return "<p style='color: red;'>Error: Line count cannot exceed 10000 for performance reasons.</p>"
        except ValueError:
            return "<p style='color: red;'>Error: Invalid line count specified.</p>"

        nodeIP, portNumber = redisNode.split(':')

        # Find the node details in pareNodes
        node_details = None
        node_index = -1

        for i, node in enumerate(pareNodes):
            if node[0][0] == nodeIP and node[1][0] == portNumber and node[4]:  # Check if active
                node_details = node
                node_index = i + 1  # Node number is index + 1
                break

        if not node_details:
            return f"<p style='color: red;'>Error: Node {redisNode} not found or is inactive in configuration.</p>"

        # Construct the log file path based on node information
        log_file_path = f"{redisLogDir}redisN{node_index}_P{portNumber}.log"

        # Check if server is reachable
        if not pingServer(nodeIP):
            return f"<p style='color: red;'>Error: Server {nodeIP} is not reachable.</p>"

        # Get the log content
        if nodeIP == pareServerIp:
            # Local server
            cmd = f"tail -n {line_count} {log_file_path}"
            status, output = subprocess.getstatusoutput(cmd)
        else:
            # Remote server
            cmd = f"ssh -q -o \"StrictHostKeyChecking no\" {pareOSUser}@{nodeIP} -C \"tail -n {line_count} {log_file_path}\""
            status, output = subprocess.getstatusoutput(cmd)

        if status != 0:
            # Use error-message class for consistency
            return f"""
            <div class="error-message">
                <p>Error retrieving log file: {log_file_path}</p>
                <p>Error message: {output}</p>
                <p>Make sure the Redis log file exists and is accessible.</p>
            </div>
            """

        # Format the log content for HTML display using classes
        log_lines = output.splitlines()
        formatted_logs = []

        for line in log_lines:
            # Apply classes for different log levels
            if "warning" in line.lower():
                # Use class, remove inline style
                formatted_line = f"<span class='log-warning'>{line}</span>"
            elif "error" in line.lower() or "fail" in line.lower():
                # Use class, remove inline style
                formatted_line = f"<span class='log-error'>{line}</span>"
            else:
                # No specific class needed for normal lines, but preserve spaces
                # Use a span to ensure consistent styling application if needed later
                formatted_line = f"<span>{line.replace(' ', '&nbsp;')}</span>"

            formatted_logs.append(formatted_line)

        log_content = "<br>".join(formatted_logs)

        return f"""
        <div>
                {log_content if log_content else "<span>No specific log output captured.</span>"}
        </div>
        """

    except Exception as e:
        return f"<p style='color: red;'>An unexpected error occurred: {str(e)}</p>"


def add_delete_node_wv(operation, node_info=None):
    """
    Adds or deletes a Redis node from the cluster via web interface.

    Args:
        operation: Either 'add' or 'del'
        node_info: For 'add', a dictionary containing node details
                  For 'del', a string with the node ID to delete

    Returns:
        HTML-formatted result of the operation
    """
    # Declare logWrite as global before any use of it
    global logWrite
    global pareNodes

    try:
        if operation == 'add':
            if not node_info:
                return "<p style='color: red;'>Error: Missing node information</p>"

            serverIP = node_info.get('serverIP', '')
            serverPORT = node_info.get('serverPORT', '')
            maxMemSize = node_info.get('maxMemSize', '')
            cpuCoreIDs = node_info.get('cpuCoreIDs', '')
            nodeType = node_info.get('nodeType', '')
            masterID = node_info.get('masterID', '')

            # Input validation
            if not validIP(serverIP):
                return "<p style='color: red;'>Error: Invalid server IP</p>"

            if not serverPORT.isdigit():
                return "<p style='color: red;'>Error: Invalid port number</p>"

            # New check: Ensure port is a 4-digit number (1000-9999)
            if len(serverPORT) != 4 or int(serverPORT) < 1000:
                return "<p style='color: red;'>Error: Port number must be a 4-digit number (1000-9999)</p>"

            if not maxMemSize or not (maxMemSize[:-2].isdigit() and maxMemSize[-2:] in ['gb', 'mb']):
                return "<p style='color: red;'>Error: Invalid memory size format. Use format like '1gb' or '500mb'</p>"

            # Validate CPU core IDs
            if not all(id.strip().isdigit() for id in cpuCoreIDs.split(',')):
                return "<p style='color: red;'>Error: Invalid CPU core IDs. Use format like '1' or '3,4'</p>"

            # Additional validation for masterID when adding a slave node
            if nodeType == 'slave-specific' and (not masterID or len(masterID.strip()) == 0):
                return """
                <div>
                    <p style='color: red;'>Error: Master ID is required when adding a slave node</p>
                    <p>Please use the "View Master Nodes" button to select a valid master node ID.</p>
                </div>
                """

            # Check if node is already in use
            if pingredisNode(serverIP, serverPORT):
                return "<p style='color: red;'>Error: This IP:PORT is already used by Redis Cluster</p>"

            # Check if node is in pareNodes config
            isActive = False
            isNewServer = True
            nodeNumber = len(pareNodes) + 1

            for pareNode in pareNodes:
                nodeIP = pareNode[0][0]
                portNumber = pareNode[1][0]
                if pareNode[4]:  # If active
                    if nodeIP == serverIP:
                        isNewServer = False
                        if portNumber == serverPORT:
                            isActive = True

            if isActive:
                return "<p style='color: red;'>Error: This IP:PORT is already configured in pareNodes</p>"

            # Capture the original logWrite function to record output
            original_logWrite = logWrite
            log_messages = []

            def capture_log(*args):
                if len(args) > 1:
                    log_text = str(args[1])
                    log_messages.append(log_text)
                original_logWrite(*args)

            # Set our capturing function
            globals()['logWrite'] = capture_log

            try:
                # Create directories and configuration files
                dirs_created = True
                if isNewServer:
                    dirs_created = redisDirMaker(serverIP, str(nodeNumber))
                    if not dirs_created:
                        # Restore original logWrite
                        globals()['logWrite'] = original_logWrite

                        # Format captured logs
                        log_output = "<br>".join([msg for msg in log_messages if msg])

                        return f"""
                        <div>
                            <h3 style='color: red;'>Failed to create directories for Redis node</h3>
                            <p>Could not create required directories on {serverIP}. Check the following:</p>
                            <ul>
                                <li>SSH access and permissions to the server</li>
                                <li>Disk space availability</li>
                                <li>Network connectivity between servers</li>
                            </ul>
                            <h4>Logs:</h4>
                            <pre style='padding: 10px; overflow-x: auto;'>{log_output}</pre>
                            <p>Please fix the issue and try again.</p>
                        </div>
                        """

                    redisBinCopied = redisBinaryCopier(serverIP, redisVersion)
                    if not redisBinCopied:
                        # Restore original logWrite
                        globals()['logWrite'] = original_logWrite

                        # Format captured logs
                        log_output = "<br>".join([msg for msg in log_messages if msg])

                        return f"""
                        <div>
                            <h3 style='color: red;'>Failed to copy Redis binaries</h3>
                            <p>Could not copy Redis binaries to {serverIP}. Check the following:</p>
                            <ul>
                                <li>SSH access and permissions to the server</li>
                                <li>Disk space availability</li>
                                <li>Ensure Redis binaries exist locally</li>
                            </ul>
                            <h4>Logs:</h4>
                            <pre style='padding: 10px; overflow-x: auto;'>{log_output}</pre>
                            <p>Please fix the issue and try again.</p>
                        </div>
                        """

                # Create and copy the config file
                conf_created = redisConfMaker(serverIP, str(nodeNumber), serverPORT, maxMemSize)
                if not conf_created:
                    # Restore original logWrite
                    globals()['logWrite'] = original_logWrite

                    # Format captured logs
                    log_output = "<br>".join([msg for msg in log_messages if msg])

                    return f"""
                    <div>
                        <h3 style='color: red;'>Failed to create or copy configuration file</h3>
                        <p>Could not create or copy the Redis configuration file to {serverIP}. Check the following:</p>
                        <ul>
                            <li>SSH access and permissions to the server</li>
                            <li>Disk space availability</li>
                            <li>Ensure the target directory exists and is writable</li>
                        </ul>
                        <h4>Logs:</h4>
                        <pre style='padding: 10px; overflow-x: auto;'>{log_output}</pre>
                        <p>Please fix the issue and try again.</p>
                    </div>
                    """

                # Start the node
                startNode(serverIP, str(nodeNumber), serverPORT, cpuCoreIDs)

                # Check if node actually started
                node_started = pingredisNode(serverIP, serverPORT)

                if not node_started:
                    # Restore original logWrite
                    globals()['logWrite'] = original_logWrite

                    # Format captured logs
                    log_output = "<br>".join([msg for msg in log_messages if msg])

                    return f"""
                    <div>
                        <h3 style='color: red;'>Failed to start Redis node</h3>
                        <p>The Redis node could not be started. Check the following:</p>
                        <ul>
                            <li>Verify that Redis binary exists at configured path: {redisBinaryDir}src/redis-server</li>
                            <li>Check disk space and permissions</li>
                            <li>Verify that the specified CPU cores ({cpuCoreIDs}) are valid and available</li>
                            <li>Check if the port {serverPORT} is available</li>
                            <li>Verify the configuration file was properly created and copied</li>
                        </ul>
                        <h4>Logs:</h4>
                        <pre style='padding: 10px; overflow-x: auto;'>{log_output}</pre>
                        <p>Please fix the issue and try again.</p>
                    </div>
                    """

                result = False
                error_message = ""

                # Add to cluster based on type
                if nodeType == 'master':
                    result = addMasterNode(serverIP, serverPORT)
                elif nodeType == 'slave-specific':
                    if masterID:
                        result = addSpecificSlaveNode(serverIP, serverPORT, masterID)
                    else:
                        # This should never happen due to our validation, but just in case
                        return "<p style='color: red;'>Error: Master ID is required for slave nodes</p>"

                # Restore original logWrite
                globals()['logWrite'] = original_logWrite

                if result:
                    # Add node to pareNodes
                    nodeStr = f"pareNodes.append([['{serverIP}'],['{serverPORT}'],['{cpuCoreIDs}'],['{maxMemSize}'],True])"
                    fileAppendWrite("pareNodeList.py", f'\n#### This node was added by paredicma web UI at {get_datetime()}\n{nodeStr}')

                    # Reload the node configuration
                    reload_success, reload_msg = reload_pare_nodes()

                    # Add node type and master info for better feedback
                    type_info = "master" if nodeType == "master" else f"slave (assigned to master {masterID})"

                    return f"""
                    <div>
                        <p style='color: green;'>Successfully added node to cluster</p>
                        <ul>
                            <li><strong>IP:PORT:</strong> {serverIP}:{serverPORT}</li>
                            <li><strong>Type:</strong> {type_info}</li>
                            <li><strong>Memory:</strong> {maxMemSize}</li>
                            <li><strong>CPU Cores:</strong> {cpuCoreIDs}</li>
                        </ul>
                        <p>The node has been added to the Redis cluster and the configuration has been updated.</p>
                    </div>
                    """
                else:
                    # Format captured logs
                    log_output = "<br>".join([msg for msg in log_messages if msg])

                    return f"""
                    <div>
                        <p style='color: red;'>Failed to add node to cluster</p>
                        <p>The Redis node was started successfully, but could not be added to the cluster.</p>
                        <h4>Logs:</h4>
                        <pre style='padding: 10px; overflow-x: auto;'>{log_output}</pre>
                    </div>
                    """
            finally:
                # Ensure we restore the original logWrite function
                globals()['logWrite'] = original_logWrite

        elif operation == 'del':
            node_id = node_info  # For delete, node_info is the node ID

            if not node_id or not node_id.isdigit():
                return "<p style='color: red;'>Error: Invalid node ID - must be a number</p>"

            node_id_int = int(node_id)

            # Verify node index exists and node is active
            if node_id_int < 1 or node_id_int > len(pareNodes):
                return f"<p style='color: red;'>Error: Node ID {node_id} doesn't exist. Valid range is 1-{len(pareNodes)}</p>"

            if not pareNodes[node_id_int - 1][4]:
                return f"<p style='color: red;'>Error: Node {node_id} is already marked as inactive</p>"

            # Get node details before deletion
            try:
                serverIP = pareNodes[node_id_int - 1][0][0]
                serverPORT = pareNodes[node_id_int - 1][1][0]
                cpuCoreIDs = pareNodes[node_id_int - 1][2][0]
                maxMemSize = pareNodes[node_id_int - 1][3][0]
            except (IndexError, KeyError) as e:
                return f"<p style='color: red;'>Error accessing node details for node {node_id}: {str(e)}</p>"

            # Capture logs during deletion
            original_logWrite = logWrite
            log_messages = []

            def capture_log(*args):
                if len(args) > 1:
                    log_text = str(args[1])
                    log_messages.append(log_text)
                original_logWrite(*args)

            # Set capturing function
            globals()['logWrite'] = capture_log

            try:
                # Check if the node is a master or slave before deletion
                is_master = False
                has_slave = False
                node_role = "unknown"

                # Only check if the node is pingable
                if pingredisNode(serverIP, serverPORT):
                    role_status = slaveORMasterNode(serverIP, serverPORT)
                    is_master = (role_status == 'M')
                    node_role = "master" if is_master else "slave" if role_status == 'S' else "unknown"

                    if is_master:
                        # Check if master has slaves
                        pingStatus, pingResponse = subprocess.getstatusoutput(
                            redisConnectCmd(serverIP, serverPORT, ' info replication | grep connected_slaves '))
                        has_slave = (pingStatus == 0 and pingResponse.find(':0') == -1)

                log_messages.append(f"Detected node {serverIP}:{serverPORT} as: {node_role}")
                if is_master:
                    log_messages.append(f"Master has slaves: {'Yes' if has_slave else 'No'}")

                # Attempt to delete from cluster
                deletion_successful = delPareNode(node_id)

                # If deletion was successful, stop the Redis process without interactive prompts
                process_stopped = False
                if deletion_successful:
                    log_messages.append(f"Stopping Redis process for node {serverIP}:{serverPORT}...")
                    try:
                        # Call stopNode with non_interactive=True
                        stopNode(serverIP, str(node_id_int), serverPORT, non_interactive=True)
                        process_stopped = True
                        log_messages.append(f"Redis process for node {serverIP}:{serverPORT} successfully terminated.")
                    except Exception as stop_error:
                        log_messages.append(f"Warning: Could not stop Redis process: {str(stop_error)}")

                # Restore original logWrite
                globals()['logWrite'] = original_logWrite

                # Format log messages
                log_output = "<br>".join([msg for msg in log_messages if msg])

                if deletion_successful:
                    # Update pareNodeList.py file
                    try:
                        # Construct old and new values
                        oldVal = f"pareNodes.append([['{serverIP}'],['{serverPORT}'],['{cpuCoreIDs}'],['{maxMemSize}'],True])"
                        newVal = f"pareNodes.append([['{serverIP}'],['{serverPORT}'],['{cpuCoreIDs}'],['{maxMemSize}'],False])"

                        log_messages.append(f"Attempting to update pareNodeList.py...")

                        # Apply the file change with improved error handling
                        file_updated = changePareNodeListFile(oldVal, newVal)

                        if file_updated:
                            log_messages.append("File update operation successful")

                            # Set the node as inactive in memory immediately
                            pareNodes[node_id_int - 1][4] = False

                            # Verification already done in changePareNodeListFile
                            log_messages.append(f"Node marked as inactive in configuration")
                        else:
                            log_messages.append("Warning: Primary file update method failed!")
                            log_messages.append("Attempting secondary update method...")

                            # Improved fallback approach
                            try:
                                # Read current file content
                                current_content = fileReadFull("pareNodeList.py")

                                # Try to find the exact line to replace
                                import re
                                pattern = fr"pareNodes\.append\(\[\['{re.escape(serverIP)}'\],\s*\['{re.escape(serverPORT)}'\],\s*\['{re.escape(cpuCoreIDs)}'\],\s*\['{re.escape(maxMemSize)}'\],\s*True\]\)"

                                # Store original line for logging
                                exact_match = re.search(pattern, current_content)
                                if exact_match:
                                    exact_old_value = exact_match.group(0)
                                    updated_content = current_content.replace(exact_old_value, newVal)
                                else:
                                    # If regex fails, try simple replace as last resort
                                    exact_old_value = oldVal
                                    updated_content = current_content.replace(oldVal, newVal)

                                # Write the updated content with proper old/new value logging
                                with open("pareNodeList.py", "w") as f:
                                    f.write(updated_content + '\n#### Node list File was Changed by paredicma at ' + get_datetime() +
                                           f'\n#### old value:{exact_old_value}' +
                                           f'\n#### new value:{newVal}' +
                                           '\n#### Fallback file edit at ' + get_datetime())
                                    f.flush()
                                    os.fsync(f.fileno())

                                # Set node as inactive in memory
                                pareNodes[node_id_int - 1][4] = False

                                log_messages.append("Fallback file update completed")
                            except Exception as fallback_error:
                                log_messages.append(f"Fallback update failed: {str(fallback_error)}")
                                log_messages.append("Please update pareNodeList.py manually to mark the node as inactive")
                    except Exception as config_error:
                        return f"""
                        <div>
                            <p style='color: orange;'>Node was deleted from cluster, but failed to update config file</p>
                            <p>Error: {str(config_error)}</p>
                            <p>You may need to manually update the pareNodeList.py file.</p>
                            <h4>Deletion Details:</h4>
                            <pre style='padding: 10px; overflow-x: auto;'>{log_output}</pre>
                        </div>
                        """

                    # Reload the node configuration to ensure all references are updated
                    reload_success, reload_msg = reload_pare_nodes()

                    # Add node role info to the message
                    node_type = f"<span style='color: {'#001f3f' if node_role == 'slave' else 'green' if node_role == 'master' else 'gray'};'>{node_role.capitalize()}</span>"
                    process_status = "<span style='color: green;'>Redis process successfully terminated</span>" if process_stopped else "<span style='color: orange;'>Redis process may still be running</span>"

                    return f"""
                    <div>
                        <p style='color: green;'>Successfully deleted node from cluster</p>
                        <ul>
                            <li><strong>Node ID:</strong> {node_id}</li>
                            <li><strong>IP:PORT:</strong> {serverIP}:{serverPORT}</li>
                            <li><strong>Node Type:</strong> {node_type}</li>
                            <li><strong>Process Status:</strong> {process_status}</li>
                        </ul>
                        <p>The node has been deleted from the Redis cluster and pareNodeList.py has been updated.</p>
                        <h4>Deletion Details:</h4>
                        <pre style='padding: 10px; overflow-x: auto;'>{log_output}</pre>
                    </div>
                    """
                else:
                    return f"""
                    <div>
                        <p style='color: red;'>Failed to delete node from cluster.</p>
                        <p>This could be because the node is a non-empty master node. Try to migrate data away from this node first or use the CLI tool for more options.</p>
                        <h4>Error Details:</h4>
                        <pre style='padding: 10px; overflow-x: auto;'>{log_output}</pre>
                    </div>
                    """
            finally:
                # Ensure we restore the original logWrite function
                globals()['logWrite'] = original_logWrite
        else:
            return "<p style='color: red;'>Error: Invalid operation. Must be 'add' or 'del'.</p>"

    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return f"""
        <div>
            <p style='color: red;'>An unexpected error occurred: {str(e)}</p>
            <pre style='padding: 10px; overflow-x: auto; font-size: 12px;'>{trace}</pre>
            <p>Please report this error to the administrator.</p>
        </div>
            """


def move_slots_wv(nodeNumber, fromNodeID, toNodeID, numberOfSlots):
    """
    Web interface function to move slots between nodes in the Redis cluster.

    Args:
        nodeNumber: The node number to use as a contact point
        fromNodeID: Source node ID to move slots from
        toNodeID: Destination node ID to move slots to
        numberOfSlots: Number of slots to move

    Returns:
        HTML-formatted result of the operation
    """
    global logWrite

    try:
        # Validate the input parameters
        try:
            numberOfSlots_int = int(numberOfSlots)
            fromNodeID_str = str(fromNodeID)
            toNodeID_str = str(toNodeID)
        except ValueError as e:
            return f"""
            <div class="error-message">
                <p>Invalid input parameters: {str(e)}</p>
                <p>Please provide valid node IDs and number of slots.</p>
            </div>
            """

        # Capture logs during the operation
        original_logWrite = logWrite
        log_messages = []

        def capture_log(*args):
            if len(args) > 1:
                log_text = str(args[1])
                log_messages.append(log_text)
            original_logWrite(*args)  # Call the original logWrite as well

        # Replace the global logWrite function
        globals()['logWrite'] = capture_log

        try:
            # Get contact node information
            if nodeNumber <= 0 or nodeNumber > len(pareNodes):
                return f"""
                <div class="error-message">
                    <p>Invalid contact node number: {nodeNumber}</p>
                    <p>Please ensure there is at least one active node in the cluster.</p>
                </div>
                """

            nodeIP = pareNodes[nodeNumber - 1][0][0]
            portNumber = pareNodes[nodeNumber - 1][1][0]

            # First display current slot information
            log_messages.append(f"Getting slot information from node {nodeIP}:{portNumber}")

            # Verify node IDs exist in the cluster
            node_check_cmd = f"{redisBinaryDir}src/redis-cli --cluster check {nodeIP}:{portNumber}"
            if redisPwdAuthentication == 'on':
                node_check_cmd += f" -a {redisPwd}"

            try:
                nodes_output = subprocess.check_output(node_check_cmd, shell=True).decode()
                # Check if fromNodeID and toNodeID are valid
                if fromNodeID_str not in nodes_output:
                    return f"""
                    <div class="error-message">
                        <p>Source node ID '{fromNodeID_str}' not found in the cluster.</p>
                        <p>Please verify the node ID and try again.</p>
                    </div>
                    """
                if toNodeID_str not in nodes_output:
                    return f"""
                    <div class="error-message">
                        <p>Destination node ID '{toNodeID_str}' not found in the cluster.</p>
                        <p>Please verify the node ID and try again.</p>
                    </div>
                    """
            except subprocess.CalledProcessError as e:
                return f"""
                <div class="error-message">
                    <p>Error verifying node IDs: {str(e)}</p>
                    <p>Please ensure the cluster is accessible and try again.</p>
                </div>
                """

            # Execute reshardCluster function
            log_messages.append(f"Starting slot migration: Moving {numberOfSlots} slots from node {fromNodeID_str} to node {toNodeID_str}")

            # Call the existing reshardCluster function
            result = reshardCluster(nodeNumber, fromNodeID_str, toNodeID_str, numberOfSlots)

            # Check result and format the response
            if result:
                # Format captured logs
                log_output = "<br>".join([msg.replace('\n', '<br>') for msg in log_messages])

                return f"""
                <div class="response-container">
                    <h3>Slot Migration Complete</h3>
                    <p style="color: green;">Successfully moved {numberOfSlots} slots from node {fromNodeID_str} to node {toNodeID_str}</p>
                    <div class="log-section">
                        <h4>Operation Log:</h4>
                        <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto;">{log_output}</pre>
                    </div>
                    <p>Note: You may need to refresh the slot information to see the updated distribution.</p>
                </div>
                """
            else:
                # Format captured logs for error case
                log_output = "<br>".join([msg.replace('\n', '<br>') for msg in log_messages])

                return f"""
                <div class="error-message">
                    <h3>Slot Migration Failed</h3>
                    <p>Failed to move {numberOfSlots} slots from node {fromNodeID_str} to node {toNodeID_str}</p>
                    <div class="log-section">
                        <h4>Error Log:</h4>
                        <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto;">{log_output}</pre>
                    </div>
                    <p>Please check the logs for details and try again.</p>
                </div>
                """
        finally:
            # Restore the original logWrite function
            globals()['logWrite'] = original_logWrite

    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return f"""
        <div class="error-message">
            <h3>Unexpected Error</h3>
            <p>An error occurred during slot migration: {str(e)}</p>
            <pre style="font-size: 12px;">{trace}</pre>
            <p>Please report this issue to the administrator.</p>
        </div>
        """


def slotInfoSimplified_wv(nodeIP, portNumber):
    """
    Returns a simplified version of the slot information, focused on just the master nodes
    and cluster slot summary - specifically for the maintenance page.
    """
    try:
        html_content = f"""
        <h2 class="section-title">Cluster Information from RedisNode: {nodeIP}:{portNumber}</h2>
        """

        # Collect master nodes information and slot information
        try:
            master_nodes_output = subprocess.check_output(
                redisConnectCmd(nodeIP, portNumber, ' CLUSTER NODES | grep master'),
                shell=True).decode()

            # Get cluster check information for slots, keys and replicas
            clusterString = f"{redisBinaryDir}src/redis-cli --cluster check {nodeIP}:{portNumber}"
            if redisPwdAuthentication == 'on':
                clusterString += f" -a {redisPwd}"

            check_output = subprocess.check_output(clusterString, shell=True).decode()

            # Extract the summary information from the check output
            node_stats = {}  # Dictionary to store node stats keyed by node ID

            # Parse the cluster check output for stats
            for line in check_output.split('\n'):
                if '->' in line:
                    parts = line.split('->')
                    if len(parts) >= 2:
                        endpoint_part = parts[0].strip()
                        stats_part = parts[1].strip()

                        # Extract node ID (short form)
                        node_id_short = endpoint_part.split('(')[1].split('...')[0] if '(' in endpoint_part else ""

                        # Extract stats
                        keys = stats_part.split('|')[0].strip()
                        slots = stats_part.split('|')[1].strip()

                        # Store in dictionary with short node ID as key
                        node_stats[node_id_short] = {
                            'keys': keys,
                            'slots': slots
                        }

            # Now create the merged table
            html_content += """
            <h3 class="section-title">Summary of Cluster</h3>
            <table class="cluster-info-table">
                <thead>
                    <tr>
                        <th>Node ID</th>
                        <th>Endpoint</th>
                        <th>Slot Range</th>
                        <th>Slots</th>
                        <th>Keys</th>
                    </tr>
                </thead>
                <tbody>
            """

            # Process and merge information from both sources
            for line in master_nodes_output.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 8:
                    node_id = parts[0]
                    endpoint = parts[1].split('@')[0]
                    slot_range = ' '.join([part for part in parts[8:] if '-' in part or part.isdigit()])

                    # Get stats from the node_stats dictionary using the node_id prefix
                    node_id_short = node_id[:8]  # Using first 8 chars as the shortened ID
                    stats = node_stats.get(node_id_short, {'keys': 'N/A', 'slots': 'N/A',})

                    html_content += f"""
                    <tr>
                        <td><span class="node-id master-node">{node_id}</span></td>
                        <td>{endpoint}</td>
                        <td>{slot_range}</td>
                        <td>{stats['slots']}</td>
                        <td>{stats['keys']}</td>
                    </tr>
                    """

            html_content += """
                </tbody>
            </table>
            """

            # Add a note about using node IDs for moving slots
            html_content += """
            <div class="help-info">
                <p><strong>Note:</strong> To move slots between nodes, use the Node IDs shown above.</p>
            </div>
            """

        except subprocess.CalledProcessError as e:
            html_content += f"<p style='color: red;'>Error retrieving cluster information: {str(e)}</p>"

        return html_content

    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return f"""
        <div class="error-message">
            <h3>Error Retrieving Cluster Information</h3>
            <p>An error occurred: {str(e)}</p>
            <pre>{trace}</pre>
        </div>
        """

## upgrade functions
#step1 download direct from redis.io
def download_redis_version_wv(redis_filename: str):
    """
    Downloads a specific Redis version package from the official release site
    to the current working directory.

    Args:
        redis_filename: The filename of the Redis release (e.g., 'redis-7.2.4.tar.gz').

    Returns:
        An HTML string indicating the result of the download attempt.
    """
    base_url = "https://download.redis.io/releases/"
    download_url = f"{base_url}{redis_filename}"
    # Use the current working directory for downloads
    download_dir = os.getcwd()
    download_path = os.path.join(download_dir, redis_filename)

    # First check if the file already exists locally
    if os.path.exists(download_path):
        return f"""
        <div class="warning-message" id="file-exists-message">
            <p>File '{redis_filename}' already exists in '{download_dir}'!</p>
            <p>You can use the existing file for extraction and compilation.</p>
        </div>
        """

    # Construct the wget command
    # Use -P to specify the download directory
    # Use --spider to check if the file exists before downloading
    # Use -q for quiet output during download
    check_command = ['wget', '--spider', download_url]
    # No need for -nc since we've already checked if the file exists
    download_command = ['wget', '-P', download_dir, '-q', download_url]

    try:
        # Check if the file exists on the remote server
        print(f"Checking availability: {download_url}")
        check_process = subprocess.run(check_command, capture_output=True, text=True, check=False)
        if check_process.returncode != 0:
            error_message = f"File not found at {download_url} or network error."
            if "404 Not Found" in check_process.stderr:
                error_message = f"Error: Release file '{redis_filename}' not found on redis.io. Please check the version."
            return f"""
            <div class="error-message">
                <p>Download Check Failed:</p>
                <p>{error_message}</p>
                <pre>{check_process.stderr}</pre>
            </div>
            """

        # If check passes, proceed with download
        print(f"Attempting to download: {download_url} to {download_dir}")
        download_process = subprocess.run(download_command, capture_output=True, text=True, check=True)

        # Verify download
        if os.path.exists(download_path):
            return f"""
            <div class="success-message">
                <p>Successfully downloaded '{redis_filename}' to '{download_dir}'.</p>
            </div>
            """
        else:
            # This case might occur if wget succeeded (returncode 0) but the file isn't there.
            return f"""
            <div class="error-message">
                <p>Download command executed but file not found at '{download_path}'.</p>
                <pre>Wget stdout: {download_process.stdout}\nWget stderr: {download_process.stderr}</pre>
            </div>
            """

    except subprocess.CalledProcessError as e:
        # Handle cases where wget fails (e.g., network issues during download)
        return f"""
        <div class="error-message">
            <p>Error downloading '{redis_filename}':</p>
            <pre>{e.stderr}</pre>
        </div>
        """
    except FileNotFoundError:
        return f"""
        <div class="error-message">
            <p>Error: 'wget' command not found. Please ensure wget is installed and in your system's PATH.</p>
        </div>
        """
    except Exception as e:
        trace = traceback.format_exc()
        return f"""
        <div class="error-message">
            <p>An unexpected error occurred during download:</p>
            <pre>{str(e)}\n{trace}</pre>
        </div>
        """


#upload from local
def upload_redis_version_wv(upload_file, filename):
    """
    Saves an uploaded Redis version package to the project directory.

    Args:
        upload_file: The uploaded file content
        filename: The name of the uploaded file (must be in format redis-X.Y.Z.tar.gz)

    Returns:
        An HTML string indicating the result of the upload.
    """
    try:
        # Validate filename format
        import re
        if not re.match(r'^redis-\d+\.\d+\.\d+\.tar\.gz$', filename):
            return """
            <div class="error-message">
                <p>Invalid Redis package filename format.</p>
                <p>The filename must be in the format: redis-X.Y.Z.tar.gz (e.g., redis-7.2.4.tar.gz)</p>
            </div>
            """

        # Use the current working directory for storing uploads
        download_dir = os.getcwd()
        file_path = os.path.join(download_dir, filename)

        # Check if file already exists
        if os.path.exists(file_path):
            return f"""
            <div class="warning-message" id="file-exists-message">
                <p>File {filename} already exists!</p>
                <p>You can use the existing file for extraction and compilation.</p>
            </div>
            """

        # Save the file
        with open(file_path, "wb") as f:
            f.write(upload_file)

        # Return success message
        return f"""
        <div class="success-message">
            <p>Successfully uploaded {filename}</p>
            <p>The file is ready for extraction and compilation.</p>
        </div>
        """

    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return f"""
        <div class="error-message">
            <p>Error uploading file: {str(e)}</p>
            <pre>{trace}</pre>
        </div>
        """


#step1 extract & compile
def extract_compile_redis_wv(redis_tarfile):
    """
    Extract and compile Redis from a previously downloaded tarball for web UI.
    Then copy the compiled binaries to the redisBinaryBase directory.
    Returns HTML content with the operation results.
    """
    try:
        # Extract version number from filename (e.g. redis-7.2.4.tar.gz -> 7.2.4)
        import re
        version_match = re.search(r'redis-([0-9]+\.[0-9]+\.[0-9]+)', redis_tarfile)
        if not version_match:
            return f"""
            <div class="error-message">
                <p style="color: orange; font-weight: bold;">Invalid Redis package filename format.</p>
                <p>The filename must be in the format: redis-X.Y.Z.tar.gz (e.g., redis-7.2.4.tar.gz)</p>
            </div>
            """

        redis_version = version_match.group(1)

        # Check if file exists
        if not os.path.exists(redis_tarfile):
            return f"""
            <div class="error-message">
                <p style="color: orange; font-weight: bold;">File not found!</p>
                <p>The file {redis_tarfile} does not exist in the current directory.</p>
            </div>
            """

        # Extract the tarball
        logWrite(pareLogFile, f"Extracting {redis_tarfile}...")
        extract_cmd = f"tar -xf {redis_tarfile}"
        extract_status, extract_output = subprocess.getstatusoutput(extract_cmd)

        if extract_status != 0:
            return f"""
            <div class="error-message">
                <p style="color: orange; font-weight: bold;">Extraction Failed!</p>
                <p>Failed to extract {redis_tarfile}. Error output:</p>
                <pre style="padding: 10px; border-left: 4px solid orange;">{extract_output}</pre>
            </div>
            """

        # Compile Redis
        logWrite(pareLogFile, f"Compiling Redis {redis_version}...")
        compile_cmd = f"cd redis-{redis_version} && make"
        compile_status, compile_output = subprocess.getstatusoutput(compile_cmd)

        if compile_status != 0:
            return f"""
            <div class="error-message">
                <p style="color: orange; font-weight: bold;">Compilation Failed!</p>
                <p>Failed to compile Redis {redis_version}. Error output:</p>
                <pre style="padding: 10px; border-left: 4px solid orange;">{compile_output}</pre>
            </div>
            """

        # Successful compilation
        logWrite(pareLogFile, f"Redis {redis_version} compiled successfully")

        # Create target directory if it doesn't exist
        target_dir = f"{redisBinaryBase}redis-{redis_version}"
        os.makedirs(os.path.dirname(target_dir), exist_ok=True)

        # Copy the compiled binaries to the redisBinaryBase directory
        logWrite(pareLogFile, f"Copying Redis {redis_version} to {target_dir}...")
        rsync_cmd = f"rsync -a --delete redis-{redis_version}/ {target_dir}/"
        copy_status, copy_output = subprocess.getstatusoutput(rsync_cmd)

        if copy_status != 0:
            return f"""
            <div class="warning-message">
                <h4 style="color: orange; font-weight: bold;">Compilation Successful, But Copy Failed</h4>
                <p>Redis {redis_version} compiled successfully, but failed to copy to {target_dir}. Error output:</p>
                <pre style="padding: 10px; border-left: 4px solid orange;">{copy_output}</pre>
            </div>
            """

        return f"""
        <div class="success-message">
            <h4 style="color: green; font-weight: bold;">Redis {redis_version} Compiled Successfully</h4>
            <p style="color: green;">Redis version {redis_version} has been extracted and compiled successfully.</p>
            <div class="code-output" style="padding: 10px; border-left: 4px solid green;">
                <p>✓ Extracted: {redis_tarfile}</p>
                <p>✓ Compiled: redis-{redis_version}</p>
                <p>✓ Copied to: {target_dir}</p>
                <p>✓ Binary location: {target_dir}/src/</p>
            </div>
        </div>
        """

    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return f"""
        <div class="error-message">
            <h4 style="color: orange; font-weight: bold;">Unexpected Error</h4>
            <p>An error occurred while extracting and compiling Redis:</p>
            <p style="color: orange;">{str(e)}</p>
            <pre style="padding: 10px; border-left: 4px solid orange;">{trace}</pre>
        </div>
        """


#step2 extract & compile
def redisNewBinaryCopier_wv(redis_version):
    """
    Copies newly compiled Redis binaries to all servers in the cluster.
    Copies to each unique server IP only once, skipping pareServerIp.

    Args:
        redis_version: The version of Redis to copy (e.g., 7.2.4)

    Returns:
        HTML-formatted result of the operation
    """
    try:
        # Validate version format
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', redis_version):
            return f"""
            <div class="error-message">
                <p style="color: orange; font-weight: bold;">Invalid Redis Version Format</p>
                <p>The version must be in the format X.Y.Z (e.g., 7.2.4)</p>
            </div>
            """

        # Construct source directory path
        source_dir = f"{redisBinaryBase}redis-{redis_version}/"

        # Check if the source directory exists
        if not os.path.exists(source_dir):
            return f"""
            <div class="error-message">
                <p style="color: orange; font-weight: bold;">Source Directory Not Found</p>
                <p>The Redis {redis_version} binaries directory was not found at:</p>
                <p>{source_dir}</p>
                <p>Please compile Redis {redis_version} first.</p>
            </div>
            """

        # Results container
        results = []
        successful_copies = 0
        failed_copies = 0
        skipped_servers = 0

        # Collect unique server IPs to avoid redundant copying
        unique_servers = set()
        for node in pareNodes:
            if node[4]:  # Only consider active nodes
                unique_servers.add(node[0][0])

        # Remove the host server from the list
        if pareServerIp in unique_servers:
            unique_servers.remove(pareServerIp)
            results.append(f"<p>⏭️ Skipping host server {pareServerIp} as binaries are already there</p>")
            skipped_servers += 1

        # Copy binaries to each unique server
        for server_ip in unique_servers:
            # Check if server is reachable
            if not pingServer(server_ip):
                results.append(f"<p style='color: orange;'>⚠️ Server {server_ip} is not reachable</p>")
                failed_copies += 1
                continue

            # Create destination directory on remote server
            dest_dir = f"{redisBinaryBase}redis-{redis_version}"
            mkdir_cmd = f"ssh {pareOSUser}@{server_ip} 'mkdir -p {dest_dir}'"
            mkdir_status, mkdir_output = subprocess.getstatusoutput(mkdir_cmd)

            if mkdir_status != 0:
                results.append(f"<p style='color: red;'>❌ Failed to create directory on {server_ip}: {mkdir_output}</p>")
                failed_copies += 1
                continue

            # Use rsync to copy files to the remote server
            rsync_cmd = f"rsync -a --delete {source_dir} {pareOSUser}@{server_ip}:{dest_dir}/"
            copy_status, copy_output = subprocess.getstatusoutput(rsync_cmd)

            if copy_status != 0:
                results.append(f"<p style='color: red;'>❌ Failed to copy Redis {redis_version} to {server_ip}: {copy_output}</p>")
                failed_copies += 1
            else:
                results.append(f"<p style='color: green;'>✅ Successfully copied Redis {redis_version} to {server_ip}</p>")
                successful_copies += 1

        # Generate the summary report
        summary = f"""
        <div class="results-summary">
            <h4>Binary Copy Summary</h4>
            <p>Total unique servers: {len(unique_servers) + skipped_servers}</p>
            <p>Successfully copied to: {successful_copies} servers</p>
            <p>Failed to copy to: {failed_copies} servers</p>
            <p>Skipped servers: {skipped_servers}</p>
        </div>
        """

        # Combine summary and detailed results
        return f"""
        <div class="operation-results">
            {summary}
            <h4>Details:</h4>
            <div class="operation-details">
                {"".join(results)}
            </div>
        </div>
        """

    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return f"""
        <div class="error-message">
            <h4 style="color: orange; font-weight: bold;">Unexpected Error</h4>
            <p>An error occurred while copying Redis binaries:</p>
            <p style="color: orange;">{str(e)}</p>
            <pre style="padding: 10px; border-left: 4px solid orange;">{trace}</pre>
        </div>
        """

#restart all slave nodes with new redis version
def restartAllSlaves_wv(wait_seconds=60, redis_version=None):
    """
    Restarts all slave nodes in the cluster with a delay between each restart.
    If redis_version is provided, updates the nodes to use that version.
    
    Args:
        wait_seconds: Number of seconds to wait between node restarts
        redis_version: Optional Redis version to upgrade to (e.g. '7.2.4')
        
    Returns:
        HTML-formatted result of the operation
    """
    results = []
    success_count = 0
    error_count = 0
    
    try:
        # Store original values to restore later
        global redisBinaryDir
        global redisVersion
        original_binary_dir = redisBinaryDir
        original_version = redisVersion

        # Update Redis version and binary directory if specified
        if redis_version:
            logWrite(pareLogFile, f"Updating Redis binary directory to use version {redis_version}")
            redisVersion = redis_version
            redisBinaryDir = f"{redisBinaryBase}redis-{redis_version}/src/"
            results.append(f"Updated Redis binary path to: {redisBinaryDir}")

        # Get slave nodes from the cluster
        slave_nodes = []
        
        # Log operation start
        log_message = f"Starting rolling restart of all slave nodes"
        if redis_version:
            log_message += f" with upgrade to Redis {redis_version}"
        logWrite(pareLogFile, log_message)
        results.append(log_message)
        
        # Find all active slave nodes
        for node_index, pareNode in enumerate(pareNodes, start=1):
            nodeIP = pareNode[0][0]
            portNumber = pareNode[1][0]
            
            if pareNode[4]:  # If node is active
                if pingredisNode(nodeIP, portNumber):
                    # Check if this is a slave node
                    if slaveORMasterNode(nodeIP, portNumber) == 'S':
                        dedicateCpuCores = pareNode[2][0]
                        slave_nodes.append({
                            'ip': nodeIP,
                            'port': portNumber,
                            'node_index': node_index,
                            'cpu_cores': dedicateCpuCores
                        })
        
        # If no slave nodes found
        if not slave_nodes:
            # Restore original binary directory
            if redis_version:
                redisBinaryDir = original_binary_dir

            return f"""
            <div class="warning-message">
                <h4 style="color: #856404; font-weight: bold;">No Slave Nodes Found</h4>
                <p>No active slave nodes were found in the cluster.</p>
                <p>You may restart master nodes separately after verifying cluster health.</p>
            </div>
            """
        
        # Process each slave node
        results.append(f"Found {len(slave_nodes)} slave nodes to restart.")
        
        for i, node in enumerate(slave_nodes):
            node_display = f"{node['ip']}:{node['port']} (Node #{node['node_index']})"
            results.append(f"Processing slave node {i+1}/{len(slave_nodes)}: {node_display}")
            
            try:
                # Check if we need to update redis.conf to use new version
                if redis_version:
                    results.append(f"Updating node {node_display} configuration to use Redis {redis_version}")
                    
                    # Construct the server path for the new Redis version
                    new_redis_path = f"{redisBinaryBase}redis-{redis_version}/src"
                    
                    # Update the configuration file path
                    conf_file = f"{redisConfigDir}{pareOSUser}_redisN{node['node_index']}_P{node['port']}.conf"
                    
                    if node['ip'] == pareServerIp:
                        # Local server
                        cmd = f"sed -i 's|^dir .*|dir {redisDataDir}{pareOSUser}_redisN{node['node_index']}_P{node['port']}/|' {conf_file} && " + \
                              f"grep -q '^server-binary' {conf_file} && " + \
                              f"sed -i 's|^server-binary .*|server-binary {new_redis_path}/redis-server|' {conf_file} || " + \
                              f"echo 'server-binary {new_redis_path}/redis-server' >> {conf_file}"
                    else:
                        # Remote server
                        cmd = f"ssh -q -o \"StrictHostKeyChecking no\" {pareOSUser}@{node['ip']} -C \"" + \
                              f"sed -i 's|^dir .*|dir {redisDataDir}{pareOSUser}_redisN{node['node_index']}_P{node['port']}/|' {conf_file} && " + \
                              f"grep -q '^server-binary' {conf_file} && " + \
                              f"sed -i 's|^server-binary .*|server-binary {new_redis_path}/redis-server|' {conf_file} || " + \
                              f"echo 'server-binary {new_redis_path}/redis-server' >> {conf_file}\""
                    
                    update_status, update_output = subprocess.getstatusoutput(cmd)
                    if update_status == 0:
                        results.append(f"<span style='color: green;'>✓ Successfully updated configuration for {node_display}</span>")
                    else:
                        results.append(f"<span style='color: orange;'>⚠ Warning: Could not update configuration: {update_output}</span>")
                
                # Perform the restart
                if redis_version:
                    results.append(f"Restarting slave node with Redis {redis_version}: {node_display}")
                    # Call restartNode with the redis_version parameter
                    restartNode(node['ip'], str(node['node_index']), node['port'], node['cpu_cores'], redis_version)
                else:
                    results.append(f"Restarting slave node with default Redis version: {node_display}")
                    # Call restartNode without specifying a version
                    restartNode(node['ip'], str(node['node_index']), node['port'], node['cpu_cores'])
                
                # Verify node is back online
                sleep(5)  # Give node time to start
                if pingredisNode(node['ip'], node['port']):
                    success_count += 1
                    results.append(f"<span style='color: green;'>✓ Successfully restarted {node_display}</span>")
                    
                    # Check Redis version if update was requested
                    if redis_version:
                        version_cmd = redisConnectCmd(node['ip'], node['port'], ' info server | grep redis_version')
                        version_status, version_output = subprocess.getstatusoutput(version_cmd)
                        if version_status == 0 and 'redis_version' in version_output:
                            current_version = version_output.split(':')[1].strip()
                            if current_version == redis_version:
                                results.append(f"<span style='color: green;'>✓ Node {node_display} now running Redis {current_version}</span>")
                            else:
                                results.append(f"<span style='color: orange;'>⚠ Node {node_display} running Redis {current_version} (expected {redis_version})</span>")
                        else:
                            results.append(f"<span style='color: orange;'>⚠ Could not verify Redis version for {node_display}</span>")
                else:
                    error_count += 1
                    results.append(f"<span style='color: red;'>✗ Failed to restart {node_display}</span>")
                
                # Wait between restarts if not the last node
                if i < len(slave_nodes) - 1 and wait_seconds > 0:
                    results.append(f"Waiting {wait_seconds} seconds before next restart...")
                    sleep(wait_seconds)
            
            except Exception as e:
                error_count += 1
                results.append(f"<span style='color: red;'>✗ Error processing {node_display}: {str(e)}</span>")
        
        # After all operations are complete, restore original values if needed
        if redis_version:
            # Only restore for this function's scope - the nodes should keep using new version
            redisVersion = original_version
            redisBinaryDir = original_binary_dir

        # Log completion
        logWrite(pareLogFile, f"Completed restarting slave nodes. Success: {success_count}, Errors: {error_count}")
        results.append(f"Completed slave node restart process.")
        
        # Format the results as HTML
        result_details = "<br>".join(results)
        
        if error_count == 0:
            return f"""
            <div class="success-message">
                <h4 style="color: green; font-weight: bold;">All Slave Nodes Restarted Successfully</h4>
                <p>Successfully restarted {success_count} slave nodes.</p>
                <div class="code-output" style="padding: 10px; border-left: 4px solid green; margin-top: 10px; max-height: 400px; overflow-y: auto;">
                    {result_details}
                </div>
                <p style="margin-top: 10px;">Cluster should be healthy with all slave nodes running the new version.</p>
                <p>You may restart master nodes next after verifying cluster health.</p>
            </div>
            """
        elif success_count > 0:
            return f"""
            <div class="warning-message">
                <h4 style="color: #856404; font-weight: bold;">Slave Nodes Restarted with Warnings</h4>
                <p>Restarted {success_count} slave nodes successfully. Failed to restart {error_count} nodes.</p>
                <div class="code-output" style="padding: 10px; border-left: 4px solid #856404; margin-top: 10px; max-height: 400px; overflow-y: auto;">
                    {result_details}
                </div>
                <p style="margin-top: 10px;">Please check the errors and try again for failed nodes.</p>
            </div>
            """
        else:
            return f"""
            <div class="error-message">
                <h4 style="color: red; font-weight: bold;">Failed to Restart Slave Nodes</h4>
                <p>Failed to restart any slave nodes.</p>
                <div class="code-output" style="padding: 10px; border-left: 4px solid red; margin-top: 10px; max-height: 400px; overflow-y: auto;">
                    {result_details}
                </div>
                <p style="margin-top: 10px;">Please check the errors and try again.</p>
            </div>
            """
    
    except Exception as e:
        # Make sure we restore the binary directory even if there's an exception
        if 'original_binary_dir' in locals() and redis_version:
            redisBinaryDir = original_binary_dir

        import traceback
        trace = traceback.format_exc()
        return f"""
        <div class="error-message">
            <h4 style="color: red; font-weight: bold;">Unexpected Error</h4>
            <p>An error occurred during the slave node restart process:</p>
            <p style="color: red;">{str(e)}</p>
            <pre style="padding: 10px; border-left: 4px solid red; max-height: 300px; overflow-y: auto;">{trace}</pre>
        </div>
        """

#update redisVersion in pareConfig.py
def update_redis_config_wv(new_redis_version):
    """
    Update Redis version in configuration files for web UI.
    """
    try:
        # Get current configuration
        from pareConfig import redisVersion, redisBinaryDir

        # Check if version is the same
        if new_redis_version == redisVersion:
            return f"""
            <div class="warning-message">
                <h4 style="color: orange; font-weight: bold;">No Change Required</h4>
                <p>The specified version is already the current version (Redis {new_redis_version}).</p>
            </div>
            """

        # Check if new binary directory exists
        new_binary_dir = redisBinaryDir.replace(f'redis-{redisVersion}', f'redis-{new_redis_version}')
        if not os.path.exists(new_binary_dir):
            return f"""
            <div class="error-message">
                <h4 style="color: red; font-weight: bold;">Binary Directory Not Found</h4>
                <p>The binary directory for Redis {new_redis_version} ({new_binary_dir}) does not exist.</p>
                <p>Please compile Redis {new_redis_version} first.</p>
            </div>
            """

        # Update configuration file
        success = True
        success = success and changePareConfigFile(f"redisVersion = '{redisVersion}'",
                                                 f"redisVersion = '{new_redis_version}'")
        success = success and changePareConfigFile(f"redisTarFile = 'redis-{redisVersion}.tar.gz'",
                                                 f"redisTarFile = 'redis-{new_redis_version}.tar.gz'")

        if success:
            # Get node information for display
            node_info = []
            for i, pareNode in enumerate(pareNodes, 1):
                if pareNode[4]:  # If node is active
                    nodeIP = pareNode[0][0]
                    portNumber = pareNode[1][0]
                    version_cmd = redisConnectCmd(nodeIP, portNumber, 'info server | grep redis_version')
                    _, version_output = subprocess.getstatusoutput(version_cmd)
                    node_info.append(f"<tr><td>{i}</td><td>{nodeIP}</td><td>{portNumber}</td><td>{version_output.strip()}</td></tr>")

            node_table = f"""
            <table>
                <tr>
                    <th>Node #</th>
                    <th>IP</th>
                    <th>Port</th>
                    <th>Redis Version</th>
                </tr>
                {''.join(node_info)}
            </table>
            """

            return f"""
            <div class="success-message">
                <h4 style="color: green; font-weight: bold;">Configuration Updated Successfully</h4>
                <p>Redis version in configuration updated from {redisVersion} to {new_redis_version}.</p>
                <p>Binary directory updated to: {new_binary_dir}</p>
                <p>Current node versions:</p>
                {node_table}
                <p><strong>Note:</strong> You may need to restart the application for changes to take effect.</p>
            </div>
            """
        else:
            return f"""
            <div class="error-message">
                <h4 style="color: red; font-weight: bold;">Configuration Update Failed</h4>
                <p>Failed to update Redis version in configuration files.</p>
            </div>
            """
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return f"""
        <div class="error-message">
            <h4 style="color: red; font-weight: bold;">Error Updating Configuration</h4>
            <p>Error: {str(e)}</p>
            <pre>{trace}</pre>
        </div>
        """


# redis version control
def redisNodesVersionControl_wv():
    """
    Get Redis version information for all nodes in the cluster.
    Returns HTML-formatted table showing all nodes and their Redis versions.
    """
    try:
        # Reload pareConfig to get the latest redisVersion
        import importlib
        import sys
        importlib.reload(sys.modules['pareConfig'])
        from pareConfig import redisVersion as configured_version

        # Container for results
        node_versions = []
        inconsistent_versions = False

        # Check each active node
        for i, pareNode in enumerate(pareNodes):
            nodeIP = pareNode[0][0]
            portNumber = pareNode[1][0]
            node_num = i + 1

            if not pareNode[4]:  # Skip inactive nodes
                continue

            # Get node role
            role = slaveORMasterNode(nodeIP, portNumber)
            node_role = "Master" if role == "M" else "Replica" if role == "S" else "Unknown"

            # Check if node is reachable
            if not pingredisNode(nodeIP, portNumber):
                node_versions.append({
                    "node_id": node_num,
                    "ip": nodeIP,
                    "port": portNumber,
                    "role": node_role,
                    "version": "Unreachable",
                    "status": "error"
                })
                continue

            # Get Redis version from the node
            cmd_status, cmd_output = subprocess.getstatusoutput(
                redisConnectCmd(nodeIP, portNumber, "info server | grep redis_version")
            )

            if cmd_status != 0 or "redis_version" not in cmd_output:
                node_version = "Error"
                status = "error"
            else:
                node_version = cmd_output.split(":")[1].strip()
                # Check if version matches configured version
                if node_version != configured_version:
                    status = "warning"
                    inconsistent_versions = True
                else:
                    status = "ok"

            node_versions.append({
                "node_id": node_num,
                "ip": nodeIP,
                "port": portNumber,
                "role": node_role,
                "version": node_version,
                "status": status
            })

        # Format the HTML output
        html_output = f"""
        <div class="version-control-container">
            <h3>Redis Version Control</h3>
            <div class="version-summary">
                <p>Configured Redis Version: <strong>{configured_version}</strong></p>
                <p class="{'warning-text' if inconsistent_versions else ''}">
                    {("⚠️ Inconsistent versions detected" if inconsistent_versions else "✓ All nodes running configured version")}
                </p>
            </div>
            
            <table class="version-table">
                <thead>
                    <tr>
                        <th>Node #</th>
                        <th>IP:Port</th>
                        <th>Role</th>
                        <th>Version</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
        """

        for node in node_versions:
            status_class = {
                "ok": "status-ok",
                "warning": "status-warning",
                "error": "status-error"
            }.get(node["status"], "")

            status_icon = {
                "ok": "✓",
                "warning": "⚠️",
                "error": "❌"
            }.get(node["status"], "?")

            html_output += f"""
                <tr class="{status_class}">
                    <td>{node["node_id"]}</td>
                    <td>{node["ip"]}:{node["port"]}</td>
                    <td>{node["role"]}</td>
                    <td>{node["version"]}</td>
                    <td>{status_icon}</td>
                </tr>
            """

        html_output += """
                </tbody>
            </table>
            
            <div class="version-control-actions">
                <h4>Version Management</h4>
                <p>Use the upgrade tools above to update Redis version.</p>
            </div>
        </div>
        """

        return html_output

    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return f"""
        <div class="error-message">
            <h4>Error Retrieving Version Information</h4>
            <p>An error occurred: {str(e)}</p>
            <pre>{trace}</pre>
        </div>
        """
