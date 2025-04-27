# !/usr/bin/python
#paredicma webview v1.0
#date: 27.02.2024
#author: alperyz

import os
import subprocess

from pareNodeList import *
from pareConfig import *
from pareFunc import *

import socket
from subprocess import getstatusoutput
from time import sleep


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
                        redisnodeInfo += f"<p style='color: blue;'> Server IP: {serverIP} | Node Number: {nodenumber} | Port: {portNumber} | Status: UP</p>"
                    else:
                        redisnodeInfo += f"<p style='color: red;'> Server IP: {serverIP} | Node Number: {nodenumber} | Port: {portNumber} | Status: DOWN</p>"
                else:
                    redisnodeInfo += f"<p style='color: orange;'> Server IP: {serverIP} | Node Number: {nodenumbers.pop(0)} | Port: {portNumber} | Status: Unknown</p>"
    return redisnodeInfo


def slotInfo_wv(nodeIP, portNumber):
    cluster_info = f"<h2>Cluster Information from RedisNode: {nodeIP}:{portNumber}</h2>"
    try:

        cluster_info += "<h3>Cluster Nodes</h3>"
        cluster_info += subprocess.check_output(redisConnectCmd(nodeIP, portNumber, ' CLUSTER NODES | grep master'),
                                                shell=True).decode()

        cluster_info += "<h3>Cluster Slots Check</h3>"
        clusterString = f"{redisBinaryDir}src/redis-cli --cluster check {nodeIP}:{portNumber}"
        if redisPwdAuthentication == 'on':
            clusterString += f" -a {redisPwd}"
        cluster_info += subprocess.check_output(clusterString, shell=True).decode()
    except subprocess.CalledProcessError as e:
        cluster_info += f"<p>Error retrieving cluster information from any of the Redis Nodes</p>"

    return cluster_info

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

        # For stop action, check if the node is master and if confirmation is required
        if action.lower() == 'stop':
            is_master, has_slave = check_if_master(nodeIP, portNumber)

            if is_master and not confirmed:
                # Return a special message that requires confirmation
                if has_slave:
                    return f"""
                    <div class="confirmation-needed">
                        <p style='color: red; font-weight: bold;'>Warning: This node ({redisNode}) is a MASTER node with slaves!</p>
                        <p>Stopping this node will trigger master/slave failover.</p>
                        <p>Do you want to continue?</p>
                        <form id="confirm-action-form" action="/manager/node-action/" method="get">
                            <input type="hidden" name="redisNode" value="{redisNode}">
                            <input type="hidden" name="action" value="stop">
                            <input type="hidden" name="confirmed" value="true">
                            <button type="submit" class="confirm-btn">Yes, Stop the Node</button>
                            <a href="/manager" class="cancel-btn">Cancel</a>
                        </form>
                    </div>
                    """
                else:
                    return f"""
                    <div class="confirmation-needed">
                        <p style='color: red; font-weight: bold;'>Warning: This node ({redisNode}) is a MASTER node with NO slaves!</p>
                        <p style='color: red;'>Stopping this node will cause Redis cluster to FAIL!</p>
                        <p>Do you want to continue?</p>
                        <form id="confirm-action-form" action="/manager/node-action/" method="get">
                            <input type="hidden" name="redisNode" value="{redisNode}">
                            <input type="hidden" name="action" value="stop">
                            <input type="hidden" name="confirmed" value="true">
                            <button type="submit" class="confirm-btn">Yes, Stop the Node</button>
                            <a href="/manager" class="cancel-btn">Cancel</a>
                        </form>
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
            # For stop action with confirmation, handle it differently
            if action.lower() == 'stop' and confirmed:
                # First check if node is master and has slaves
                is_master, has_slave = check_if_master(nodeIP, portNumber)
                if is_master and has_slave:
                    log_messages.append(f"Master/slave switch process is starting for {nodeIP}:{portNumber}... This might take some time")
                    # Perform master/slave failover before stopping
                    switchMasterSlave(nodeIP, node_index, portNumber)

                # Now stop the node
                log_messages.append(f"Stopping Redis node {nodeIP}:{portNumber}")
                stopNode(nodeIP, node_num_str, portNumber)
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
            if action.lower() == 'start' or action.lower() == 'restart':
                result_message += f" Final status: {'<span style=\'color: green;\'>Running</span>' if final_ping_status else '<span style=\'color: red;\'>Not Running</span>'}."
            elif action.lower() == 'stop':
                result_message += f" Final status: {'<span style=\'color: gray;\'>Stopped</span>' if not final_ping_status else '<span style=\'color: red;\'>Still Running?</span>'}."

            # Format captured logs
            log_output = "<br>".join(log_messages).replace('\n', '<br>')  # Ensure newlines are breaks

            return f"""
                <p>{result_message}</p>
                <h4>Logs:</h4>
                <pre style='background-color: #eee; padding: 10px; border: 1px solid #ccc;'>{log_output if log_output else "No specific log output captured."}</pre>
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
            log_messages.append(f"Master/slave switch process is starting... This might take some time")

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
                    <pre style='background-color: #eee; padding: 10px; border: 1px solid #ccc;'>{log_output}</pre>
                </div>
                """
            else:
                log_output = "<br>".join(log_messages).replace('\n', '<br>')
                return f"""
                <p style='color: red; font-weight: bold;'>Failed to switch master/slave roles.</p>
                <p>Current roles: {nodeIP}:{portNumber} is {new_slave_role}, {slaveIP}:{slavePort} is {new_master_role}</p>
                <h4>Logs:</h4>
                <pre style='background-color: #eee; padding: 10px; border: 1px solid #ccc;'>{log_output}</pre>
                """

        except Exception as e:
            # Restore original logWrite in case of error
            logWrite = original_logWrite
            # Format captured logs even in case of error
            log_output_error = "<br>".join(log_messages).replace('\n', '<br>')
            return f"<p style='color: red;'>Error during master/slave switch: {e}</p><pre>{log_output_error}</pre>"

    except Exception as e:
        return f"<p style='color: red;'>An unexpected error occurred: {e}</p>"


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

