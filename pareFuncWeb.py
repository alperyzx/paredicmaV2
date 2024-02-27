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
