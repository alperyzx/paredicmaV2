# !/usr/bin/python


import os
import sys
from time import *
from pareConfig import *
from pareFunc import *
from screenMenu import *
from paredicma import *


def main():
    MenuState = 0
    ans = True
    while ans:
        if MenuState == 0:
            menuMain()
            ans = input("	What would you like to do? ")
        if ans == "1" or MenuState == 1:
            if not os.path.isfile('paredicma.done'):
                resCluster = input(
                    bcolors.WARNING + "\nRedis cluster have NOT been created yet. You DO NOT use this menu. (for "
                                      "force use 'touch paredicma.done' file)" + bcolors.ENDC)
                MenuState = 0
                menuMain()
            else:
                MenuState = 1
                menuMon()
                nodeNumber = 0
                returnVAl = input("	What would you like to do? :")
                if returnVAl == "1":  # ping Cluster nodes
                    print('Pinging Nodes...')
                    pongNumber = 0
                    nonPongNumber = 0
                    for pareNode in pareNodes:
                        nodeIP = pareNode[0][0]
                        portNumber = pareNode[1][0]
                        nodeNumber = nodeNumber + 1
                        if pareNode[4]:
                            isPing = pingNode(nodeIP, portNumber)
                            if isPing:
                                print(bcolors.OKGREEN + 'OK -> Node Number :' + str(
                                    nodeNumber) + ' Server IP :' + nodeIP + ' Port:' + portNumber + bcolors.ENDC)
                                pongNumber += 1
                            else:
                                print(bcolors.FAIL + '!!!! NOT OK -> Node Number :' + str(
                                    nodeNumber) + ' Server IP :' + nodeIP + ' Port:' + portNumber + bcolors.ENDC)
                                nonPongNumber += 1
                    returnVAl = input('\n--------------\n' + bcolors.OKGREEN + 'OK Nodes = ' + str(
                        pongNumber) + bcolors.ENDC + bcolors.FAIL + '\nNot OK Nodes = ' + str(
                        nonPongNumber) + '\n--------------' + bcolors.ENDC + '\nPress Enter to Return Paredicmon Menu')
                elif returnVAl == "2":  # list redis Nodes
                    funcNodesList()
                    print(bcolors.BOLD + 'Press Enter to Return Paredicmon Menu' + bcolors.ENDC)
                elif returnVAl == "3":  # node Info
                    infoCmd = ''
                    nodeCmd = input(
                        bcolors.BOLD + '\nPlease enter node number and cmd ("4" or "2 memory" or "3 server" or "3'
                                       'cpu" etc.) \n  nodeNumber ( and cmd ) : ' + bcolors.ENDC)
                    if nodeCmd.isdigit():
                        if int(nodeCmd) > len(pareNodes) or pareNodes[int(nodeCmd) - 1][4] is False:
                            print(bcolors.WARNING + '\nYou entered wrong node number\n' + bcolors.ENDC)
                        else:
                            nodeNumber = int(nodeCmd)
                            nodeIP = pareNodes[nodeNumber - 1][0][0]
                            portNumber = pareNodes[nodeNumber - 1][1][0]
                            nodeInfoVal = nodeInfo(nodeIP, nodeNumber, portNumber, infoCmd)
                            returnVAl = input(bcolors.BOLD + '\n------- Node Info -------\nNode Number :' + str(
                                nodeNumber) + ' Server IP :' + nodeIP + ' Port:' + portNumber + '\n' + nodeInfoVal
                                              + '\n------------------\nPress Enter to Return Paredicmon Menu' + bcolors.ENDC)
                    else:
                        nodeCmd = nodeCmd.lower()
                        cmdList = nodeCmd.split(' ')
                        if cmdList[0].isdigit() and (
                                (cmdList[1]) == 'server' or (cmdList[1]) == 'clients' or (
                                cmdList[1]) == 'memory' or (cmdList[1]) == 'persistence' or (
                                        cmdList[1]) == 'stats' or (cmdList[1]) == 'replication' or (
                                        cmdList[1]) == 'cpu' or (cmdList[1]) == 'cluster' or (
                                        cmdList[1]) == 'keyspace'):
                            if int(cmdList[0]) > len(pareNodes) or pareNodes[int(cmdList[0]) - 1][4] is False:
                                print(
                                    bcolors.WARNING + '\nYou entered wrong node number \n------------------' + bcolors.ENDC)
                            else:
                                infoCmd = cmdList[1]
                                nodeNumber = int(cmdList[0])
                                nodeIP = pareNodes[nodeNumber - 1][0][0]
                                portNumber = pareNodes[nodeNumber - 1][1][0]
                                nodeInfoVal = nodeInfo(nodeIP, nodeNumber, portNumber, infoCmd)
                                returnVAl = input(bcolors.BOLD + '\n------- Node Info -------\nNode Number :' + str(
                                    nodeNumber) + ' Server IP :' + nodeIP + ' Port:' + portNumber + '\n'
                                                                                                    '------------------\n' + nodeInfoVal +
                                                  '\n------------------\nPress Enter to Return Paredicmon Menu' + bcolors.ENDC)
                        else:
                            print(bcolors.WARNING + '\nYou entered wrong value \n------------------' + bcolors.ENDC)
                elif returnVAl == "4":  # Server Info
                    serverIP = input(bcolors.BOLD + '\n Enter server IP            :' + bcolors.ENDC)
                    if validIP(serverIP):
                        serverInfo(serverIP)
                    else:
                        print(bcolors.FAIL + '\nYou entered wrong IP number\n' + bcolors.ENDC)
                elif returnVAl == "5":  # Slot Info
                    nodeNumber = 0
                    for pareNode in pareNodes:
                        nodeIP = pareNode[0][0]
                        portNumber = pareNode[1][0]
                        nodeNumber = nodeNumber + 1
                        if pareNode[4]:
                            isPing = pingNode(nodeIP, portNumber)
                            if isPing:
                                slotInfo(nodeIP, portNumber)
                                break
                elif returnVAl == "6":  # Cluster Status
                    nodeNumber = 0
                    for pareNode in pareNodes:
                        nodeIP = pareNode[0][0]
                        portNumber = pareNode[1][0]
                        nodeNumber = nodeNumber + 1
                        if pareNode[4]:
                            isPing = pingNode(nodeIP, portNumber)
                            if isPing:
                                clusterStateInfo(nodeIP, nodeNumber, portNumber)
                    input('\n----------------------\nPress Enter to Return Paredicmon Menu')
                elif returnVAl == "7":  # Show Memory Usage
                    showMemoryUsage()
                # input('\n---- -----\nPress Enter to Return Paredicmon Menu')
                elif returnVAl == "8":  # Not Designated
                    print('hello man')
                elif returnVAl == "9":  # Main Menu
                    print("your Choise: " + returnVAl + " --- You are going to Main Menu ...")
                    MenuState = 0
                elif returnVAl == "10":  # Exit
                    print("your Choise : " + returnVAl)
                    print("\n Goodbye")
                    exit()
                else:
                    print(bcolors.WARNING + "\n !!! Not Valid Choice! Try again" + bcolors.ENDC)
                    sleep(1)
        elif ans == "2" or MenuState == 2:
            if not os.path.isfile('paredicma.done'):
                resCluster = input(
                    bcolors.WARNING + "\nRedis cluster have NOT  been created yet. You DO NOT use this menu. (for "
                                      "force use 'touch paredicma.done' file)" + bcolors.ENDC)
                MenuState = 0
                menuMain()
            else:
                MenuState = 2
                menuMan()
                returnVAl = input("	What would you like to do? :")
                if returnVAl == "1":  # Start/Stop/Restart Redis Node
                    print(bcolors.BOLD + 'Start/Stop/Restart Redis Node\n------------------\n' + bcolors.ENDC)
                    funcNodesList()
                    myNodeNum = input(bcolors.BOLD + "\nPlease Enter Node Number : " + bcolors.ENDC)
                    print('Your choise :' + bcolors.BOLD + myNodeNum + bcolors.ENDC)
                    if myNodeNum.isdigit():
                        nodeNumber = int(myNodeNum)
                        if nodeNumber <= len(pareNodes) and pareNodes[nodeNumber - 1][4]:
                            nodeIP = pareNodes[nodeNumber - 1][0][0]
                            portNumber = pareNodes[nodeNumber - 1][1][0]
                            dedicateCpuCores = pareNodes[nodeNumber - 1][2][0]
                            myOps = input(
                                bcolors.BOLD + "\nPlease Choose Operation ( Start/Stop/Restart) : " + bcolors.ENDC)
                            myOps = myOps.lower()
                            if myOps == 'start':
                                print(bcolors.BOLD + 'Node :' + myNodeNum + ' is starting...' + bcolors.ENDC)
                                startNode(nodeIP, str(nodeNumber), portNumber, dedicateCpuCores)
                            elif myOps == 'stop':
                                print(bcolors.BOLD + 'Node :' + myNodeNum + ' is stopping...' + bcolors.ENDC)
                                stopNode(nodeIP, str(nodeNumber), portNumber)
                            elif myOps == 'restart':
                                print(bcolors.BOLD + 'Node :' + myNodeNum + ' is restarting...' + bcolors.ENDC)
                                restartNode(nodeIP, str(nodeNumber), portNumber, dedicateCpuCores)
                            else:
                                print(bcolors.FAIL + '!!!You entered wrong value!!! : ' + myOps + bcolors.ENDC)
                        else:
                            print(bcolors.FAIL + '!!!You entered wrong number!!! : ' + myNodeNum + bcolors.ENDC)
                    else:
                        print(bcolors.FAIL + '!!!You entered wrong value!!! : ' + myNodeNum + bcolors.ENDC)
                    funcNodesList()
                elif returnVAl == "2":  # Switch Master/Slave Nodes
                    print(bcolors.BOLD + 'Switch Master/Slave Redis Node\n------------------\n' + bcolors.ENDC)
                    funcNodesList()
                    myNodeNum = input(bcolors.BOLD + "\nPlease Enter Master Node Number : " + bcolors.ENDC)
                    print('Your choise :' + myNodeNum)
                    if myNodeNum.isdigit():
                        nodeNumber = int(myNodeNum)
                        if nodeNumber <= len(pareNodes) and pareNodes[nodeNumber - 1][4]:
                            nodeIP = pareNodes[nodeNumber - 1][0][0]
                            portNumber = pareNodes[nodeNumber - 1][1][0]
                            dedicateCpuCores = pareNodes[nodeNumber - 1][2][0]
                            myOps = input(bcolors.WARNING + "\nAre You Sure ( yes/no) : " + bcolors.ENDC)
                            if myOps == 'yes':
                                print(bcolors.BOLD + 'Node :' + myNodeNum + ' is switching...' + bcolors.ENDC)
                                swOK = switchMasterSlave(nodeIP, nodeNumber, portNumber)
                            # if(swOK)
                            elif myOps == 'no':
                                print(bcolors.FAIL + 'Operation canceled.' + bcolors.ENDC)
                            else:
                                print(bcolors.FAIL + '!!!You entered wrong value!!! : ' + myOps + bcolors.ENDC)
                        else:
                            print(bcolors.FAIL + '!!!You entered wrong number!!! : ' + myNodeNum + bcolors.ENDC)
                    else:
                        print(bcolors.FAIL + '!!!You entered wrong value!!! : ' + myNodeNum + bcolors.ENDC)
                    funcNodesList()
                elif returnVAl == "3":  # Change Redis Configuration
                    print(bcolors.BOLD + 'Change Redis Configuration' + bcolors.ENDC)
                    funcNodesList()
                    myNodeNum = input(bcolors.BOLD + '\nPlease Enter Node Number or Enter "all": ' + bcolors.ENDC)
                    myNodeNum = myNodeNum.lower()
                    if myNodeNum.isdigit() or myNodeNum == '':
                        if myNodeNum == '':
                            myNodeNum = '40'
                        if int(myNodeNum) <= len(pareNodes) and pareNodes[int(myNodeNum) - 1][4]:
                            myConfigParameter = input(
                                bcolors.BOLD + '\nPlease Enter Configuration  parameter (for example: "slowlog-max-len'
                                               '10" ,"maxmemory 3gb" ext.) \n	: ' + bcolors.ENDC)
                            yesNo = input(
                                bcolors.WARNING + '\nAre you sure to set this parameter -> ' + myConfigParameter + '(yes/no):' + bcolors.ENDC)
                            yesNo = yesNo.lower()
                            if yesNo == 'yes':
                                nodeIP = pareNodes[int(myNodeNum) - 1][0][0]
                                portNumber = pareNodes[int(myNodeNum) - 1][1][0]
                                print(
                                    bcolors.BOLD + 'Redis configuration will change on Node Number :' + myNodeNum + 'Node IP :' + nodeIP + '  Node Port :' + portNumber + bcolors.ENDC)
                                os.system(redisConnectCmd(nodeIP, portNumber, ' CONFIG SET ' + myConfigParameter))
                            else:
                                print(bcolors.FAIL + '!!!Operation was canceled !!!' + bcolors.ENDC)

                        else:
                            print(bcolors.FAIL + '!!!You entered wrong value!!! : ' + myNodeNum + bcolors.ENDC)
                    elif myNodeNum == 'all':
                        myConfigParameter = input(
                            '\nPlease Enter Configuration  parameter (for example: "slowlog-max-len 10" ,"maxmemory '
                            '3gb" ext.) \n	: ')
                        yesNo = input('\nAre you sure to set this parameter -> ' + myConfigParameter + '  (yes/no):')
                        yesNo = yesNo.lower()
                        if yesNo == 'yes':
                            nodeNumber = 0
                            for pareNode in pareNodes:
                                nodeIP = pareNode[0][0]
                                portNumber = pareNode[1][0]
                                nodeNumber = nodeNumber + 1
                                if pareNode[4]:
                                    print('Redis configuration will change  will rewrite on Node Number :' + str(
                                        nodeNumber) + '  Node IP :' + nodeIP + '  Node Port :' + portNumber)
                                    os.system(redisConnectCmd(nodeIP, portNumber, ' CONFIG SET ' + myConfigParameter))
                        else:
                            print('!!!Operation was canceled !!!')

                    else:
                        print('!!!You entered wrong value!!! : ' + myNodeNum)
                    sleep(3)

                    sleep(3)
                elif returnVAl == "4":  # Save Redis Config to redis.conf
                    print(bcolors.BOLD + 'Save Redis Configuration to redis.conf' + bcolors.ENDC)
                    funcNodesList()
                    myNodeNum = input(bcolors.BOLD + '\nPlease Enter Node Number or "all": ' + bcolors.ENDC)
                    myNodeNum = myNodeNum.lower()
                    if myNodeNum.isdigit():
                        if int(myNodeNum) <= len(pareNodes) and pareNodes[int(myNodeNum) - 1][4]:
                            nodeIP = pareNodes[int(myNodeNum) - 1][0][0]
                            portNumber = pareNodes[int(myNodeNum) - 1][1][0]
                            print(
                                bcolors.BOLD + 'Redis config file  will rewrite on Node Number :' + myNodeNum + 'Node '
                                                                                                                'IP '
                                                                                                                ':' +
                                nodeIP + '  Node Port :' + portNumber + bcolors.ENDC)
                            os.system(redisConnectCmd(nodeIP, portNumber, ' CONFIG REWRITE'))

                        else:
                            print(bcolors.FAIL + '!!!You entered wrong value!!! : ' + myNodeNum + bcolors.ENDC)
                    elif myNodeNum == 'all':
                        nodeNumber = 0
                        for pareNode in pareNodes:
                            nodeIP = pareNode[0][0]
                            portNumber = pareNode[1][0]
                            nodeNumber = nodeNumber + 1
                            if pareNode[4]:
                                print(bcolors.BOLD + 'Redis config file  will rewrite on Node Number :' + str(
                                    nodeNumber) + '  Node IP :' + nodeIP + '  Node Port :' + portNumber + bcolors.ENDC)
                                os.system(redisConnectCmd(nodeIP, portNumber, ' CONFIG REWRITE'))
                    else:
                        print(bcolors.FAIL + '!!!You entered wrong value!!! : ' + myNodeNum + bcolors.ENDC)
                    sleep(3)
                elif returnVAl == "5":  # Rolling Restart
                    print('Rolling Restart is launching.')
                    nodeNumber = 0
                    waitSleep = input(
                        bcolors.BOLD + "\nsleep time between node restart (0 = no sleep time, minute(s) ) :" + bcolors.ENDC)
                    rebootList = ''
                    if waitSleep.isdigit():
                        for pareNode in pareNodes:
                            nodeIP = pareNode[0][0]
                            portNumber = pareNode[1][0]
                            dedicateCpuCores = pareNode[2][0]
                            nodeNumber = nodeNumber + 1
                            if pareNode[4] and isNodeMaster(nodeIP, nodeNumber, portNumber) is False:
                                print(bcolors.BOLD + 'Node Number :' + str(
                                    nodeNumber) + '  Node IP :' + nodeIP + '  Node Port :' + portNumber + bcolors.ENDC)
                                restartNode(nodeIP, str(nodeNumber), portNumber, dedicateCpuCores)
                                rebootList += 'N' + str(nodeNumber) + 'N-'
                                sleep(int(waitSleep) * 60)
                        nodeNumber = 0
                        for pareNode in pareNodes:
                            nodeIP = pareNode[0][0]
                            portNumber = pareNode[1][0]
                            dedicateCpuCores = pareNode[2][0]
                            nodeNumber = nodeNumber + 1
                            if (pareNode[4] and isNodeMaster(nodeIP, nodeNumber, portNumber) and rebootList.find(
                                    'N' + str(nodeNumber) + 'N-') == -1):
                                print(bcolors.BOLD + 'Node Number :' + str(
                                    nodeNumber) + '  Node IP :' + nodeIP + '  Node Port :' + portNumber + bcolors.ENDC)
                                restartNode(nodeIP, str(nodeNumber), portNumber, dedicateCpuCores)
                                sleep(int(waitSleep) * 60)
                    else:
                        print(bcolors.FAIL + '!!!You entered wrong value!!! : ' + waitSleep + bcolors.ENDC)
                    sleep(3)
                elif returnVAl == "6":  # Command for all nodes
                    RedisCmd = input(bcolors.BOLD + "\nPlease Enter Redis Command :" + bcolors.ENDC)
                    print("your Command :" + bcolors.WARNING + RedisCmd + bcolors.ENDC)
                    onlyMaster = input(
                        bcolors.BOLD + "\nDou you want to execute this command for !!! ONLY MASTER NODES !!! (yes/no) :" + bcolors.ENDC)
                    onlyMaster = onlyMaster.lower()
                    if onlyMaster == 'yes' or onlyMaster == 'no':
                        waitSleep = input(
                            bcolors.BOLD + "\nsleep time between command (0 = no sleep time, minute(s) ) :" + bcolors.ENDC)
                        if waitSleep.isdigit():
                            nodeNumber = 0
                            for pareNode in pareNodes:
                                nodeIP = pareNode[0][0]
                                portNumber = pareNode[1][0]
                                nodeNumber = nodeNumber + 1
                                if pareNode[4]:
                                    if isNodeMaster(nodeIP, str(nodeNumber), portNumber):
                                        print(bcolors.BOLD + 'Command will execute on Node Number :' + str(
                                            nodeNumber) + '  Node IP :' + nodeIP + '  Node Port :' + portNumber + bcolors.ENDC)
                                        os.system(redisConnectCmd(nodeIP, portNumber, RedisCmd))
                                    else:
                                        if onlyMaster == 'no':
                                            print(bcolors.BOLD + 'Command will execute on Node Number :' + str(
                                                nodeNumber) + '  Node IP :' + nodeIP + '  Node Port :' + portNumber + bcolors.ENDC)
                                            os.system(redisConnectCmd(nodeIP, portNumber, RedisCmd))
                                    sleep(int(waitSleep) * 60)
                        else:
                            print(bcolors.FAIL + '!!!You entered wrong value!!! : ' + waitSleep + bcolors.ENDC)
                    else:
                        print(bcolors.FAIL + '!!!You entered wrong value!!! : ' + onlyMaster + bcolors.ENDC)
                    myR = input(bcolors.BOLD + '\nPress Enter to continue...' + bcolors.ENDC)
                elif returnVAl == "7":  # Show Redis Log File
                    funcNodesList()
                    myNodeNum = input(bcolors.BOLD + "\nPlease Enter Node Number : " + bcolors.ENDC)
                    print('Your choise :' + bcolors.BOLD + myNodeNum + bcolors.ENDC)
                    if myNodeNum.isdigit():
                        nodeNumber = int(myNodeNum)
                        if nodeNumber <= len(pareNodes) and pareNodes[nodeNumber - 1][4]:
                            myLineNum = input(
                                bcolors.BOLD + "\nHow many line do you want to see ( 1-1000 ) ? : " + bcolors.ENDC)
                            if myLineNum.isdigit():
                                if 1000 >= int(myLineNum) > 0:
                                    nodeIP = pareNodes[nodeNumber - 1][0][0]
                                    portNumber = pareNodes[nodeNumber - 1][1][0]
                                    showRedisLogFile(nodeIP, str(nodeNumber), portNumber, myLineNum)
                                else:
                                    print(
                                        bcolors.FAIL + '!!!You entered wrong value. It must be between 1 - 1000 !!! : ' + myLineNum + bcolors.ENDC)
                            else:
                                print(bcolors.FAIL + '!!!You entered wrong value!!! : ' + myLineNum + bcolors.ENDC)
                        else:
                            print(bcolors.FAIL + '!!!You entered wrong number!!! : ' + myNodeNum + bcolors.ENDC)
                    else:
                        print(bcolors.FAIL + '!!!You entered wrong value!!! : ' + myNodeNum + bcolors.ENDC)
                elif returnVAl == "8":  # Not Designated
                    print('hello man')
                elif returnVAl == "9":  # Main Menu
                    print(
                        bcolors.BOLD + "your Choise :" + returnVAl + " --- You are going to Main Menu ..." + bcolors.ENDC)
                    MenuState = 0
                elif returnVAl == "10":  # Exit
                    print("your Choise : " + bcolors.WARNING + returnVAl + bcolors.ENDC)
                    print("\n Goodbye")
                    exit()
                else:
                    print(bcolors.FAIL + "\n !!! Not Valid Choice! Try again" + bcolors.ENDC)
                    sleep(1)
            sleep(1)
        elif ans == "3" or MenuState == 3:
            if not os.path.isfile('paredicma.done'):
                resCluster = input(
                    bcolors.WARNING + "\nRedis cluster have NOT  been created yet. You DO NOT use this menu. (for"
                                      "force use 'touch paredicma.done' file)" + bcolors.ENDC)
                MenuState = 0
                menuMain()
            else:
                MenuState = 3
                menuMum()
                returnVAl = input(bcolors.BOLD + ' What would you like to do? ' + bcolors.ENDC)
                if returnVAl == "1":  # Add/Delete Redis Node
                    global redisVersion
                    print(bcolors.BOLD + 'Add/Delete Redis Node' + bcolors.ENDC)
                    operationType = input(
                        bcolors.BOLD + '\nPlease enter operation type "1" ->add or "2" -> del:' + bcolors.ENDC)
                    operationType = operationType.lower()
                    if operationType == '1' or operationType == 'add':
                        serverIP = input(bcolors.BOLD + '\nPlease enter node IP :' + bcolors.ENDC)
                        if validIP(serverIP):
                            serverPORT = input(bcolors.BOLD + '\nPlease enter node port :' + bcolors.ENDC)
                            if serverPORT.isdigit():
                                maxMemSize = input(
                                    bcolors.BOLD + '\nPlease enter node memory size ("1gb","500mb","4gb" ext.) :' + bcolors.ENDC)
                                maxMemSize = maxMemSize.lower()
                                cpuCoreOK = True
                                cpuCoreIDs = input(
                                    bcolors.BOLD + '\nPlease enter dedicate cpu core id(s)  ("1" or "3" or "4,5" or  '
                                                   '"8,9,10,11" ext.) :' + bcolors.ENDC)
                                coreList = cpuCoreIDs.split(',')
                                for coreId in coreList:
                                    if not coreId.isdigit():
                                        cpuCoreOK = False
                                if (maxMemSize[:len(maxMemSize) - 2].isdigit() and (
                                        (maxMemSize[len(maxMemSize) - 2:]) == 'gb' or (
                                        maxMemSize[len(maxMemSize) - 2:]) == 'mb')):
                                    if pingNode(serverIP, serverPORT) and cpuCoreOK:
                                        print(
                                            bcolors.FAIL + '!!! This IP(' + serverIP + '):Port(' + serverPORT + ') is '
                                                                                                                'already used by Redis Cluster !!!\n Operation canceled !!!' + bcolors.ENDC)
                                    else:
                                        isActive = False
                                        isNewServer = True
                                        nodeNumber = len(pareNodes) + 1
                                        for pareNode in pareNodes:
                                            nodeIP = pareNode[0][0]
                                            portNumber = pareNode[1][0]
                                            if pareNode[4]:
                                                if nodeIP == serverIP:
                                                    isNewServer = False
                                                    if portNumber == serverPORT:
                                                        isActive = True
                                        nodeStr = ''
                                        if not isActive:
                                            if isNewServer:
                                                redisDirMaker(serverIP, str(nodeNumber))
                                                redisBinaryCopier(serverIP, redisVersion)
                                                redisConfMaker(serverIP, str(nodeNumber), serverPORT, maxMemSize)
                                            else:
                                                redisDirMaker(serverIP, str(nodeNumber))
                                                redisConfMaker(serverIP, str(nodeNumber), serverPORT, maxMemSize)
                                            startNode(serverIP, str(nodeNumber), serverPORT, cpuCoreIDs)
                                            willbeMasterNode = input(
                                                bcolors.BOLD + '\nDo you want to set this node as MASTER (yes/no):' + bcolors.ENDC)
                                            willbeMasterNode = willbeMasterNode.lower()
                                            if willbeMasterNode == 'yes':
                                                if addMasterNode(serverIP, serverPORT):
                                                    nodeStr = "pareNodes.append([['" + serverIP + "'],['" + serverPORT + "'],['" + cpuCoreIDs + "'],['" + maxMemSize + "'],True])"
                                                    fileAppendWrite("pareNodeList.py",
                                                                    '#### This node was added by paredicma at ' + get_datetime() + '\n' + nodeStr)
                                                    pareNodes.append(
                                                        [[serverIP], [serverPORT], [cpuCoreIDs], [maxMemSize], True])
                                                    print(
                                                        bcolors.OKGREEN + 'Slave Node was added to Cluster\n' + nodeStr + bcolors.ENDC)
                                                    funcNodesList()
                                                else:
                                                    print(
                                                        bcolors.FAIL + '!!! Problem occurred  while processing.. !!!\n' + nodeStr + bcolors.ENDC)
                                                    input(bcolors.BOLD + '\nPress enter to continue...' + bcolors.ENDC)
                                            elif willbeMasterNode == 'no':
                                                willbeSSNode = input(
                                                    bcolors.BOLD + '\nDo you want to set this node SLAVE for Specific'
                                                                   'master node (yes/no):' + bcolors.ENDC)
                                                willbeSSNode = willbeSSNode.lower()
                                                if willbeSSNode == 'yes':
                                                    getMasterNodesID()
                                                    cMasterID = input(
                                                        bcolors.BOLD + '\nPlease enter master node id :' + bcolors.ENDC)
                                                    if addSpecificSlaveNode(serverIP, serverPORT, cMasterID):
                                                        nodeStr = "pareNodes.append([['" + serverIP + "'],['" + serverPORT + "'],['" + cpuCoreIDs + "'],['" + maxMemSize + "'],True])"
                                                        fileAppendWrite("pareNodeList.py",
                                                                        '#### This node was added by paredicma at ' + get_datetime() + '\n' + nodeStr)
                                                        pareNodes.append(
                                                            [[serverIP], [serverPORT], [cpuCoreIDs], [maxMemSize],
                                                             True])
                                                        print(
                                                            bcolors.OKGREEN + 'Slave Node was added to Cluster\n'
                                                            + nodeStr + bcolors.ENDC)
                                                        funcNodesList()
                                                    else:
                                                        print(
                                                            bcolors.FAIL + '!!! Problem occurred  while processing.. '
                                                                           '!!!\n' + nodeStr + bcolors.ENDC)
                                                        input('\nPress enter to continue...' + bcolors.ENDC)
                                                elif willbeSSNode == 'no':
                                                    if addSlaveNode(serverIP, serverPORT):
                                                        nodeStr = "pareNodes.append([['" + serverIP + "'],['" + serverPORT + "'],['" + cpuCoreIDs + "'],['" + maxMemSize + "'],True])"
                                                        fileAppendWrite("pareNodeList.py",
                                                                        '#### This node was added by paredicma at '
                                                                        + get_datetime() + '\n' + nodeStr)
                                                        pareNodes.append(
                                                            [[serverIP], [serverPORT], [cpuCoreIDs], [maxMemSize],
                                                             True])
                                                        print(
                                                            bcolors.OKGREEN + 'Slave Node was added to Cluster\n' + nodeStr + bcolors.ENDC)
                                                        funcNodesList()
                                                    else:
                                                        print(
                                                            bcolors.FAIL + '!!! Problem occurred  while proccesing.. '
                                                                           '!!!\n' + nodeStr + bcolors.ENDC)
                                                        input(
                                                            bcolors.BOLD + '\nPress enter to continue...' + bcolors.ENDC)

                                                else:
                                                    print(
                                                        bcolors.FAIL + '\nYou entered wrong value :' + willbeSSNode + bcolors.ENDC)
                                            else:
                                                print(
                                                    bcolors.FAIL + '\nYou entered wrong value :' + willbeMasterNode + bcolors.ENDC)


                                        else:
                                            print(
                                                bcolors.FAIL + '!!! This IP(' + serverIP + '):Port(' + serverPORT + ') is already used by pareNodes config !!!\n Operation canceled !!!' + bcolors.ENDC)
                                else:
                                    print(
                                        bcolors.FAIL + '\nYou entered wrong memory size or cpu core id(s)  mem :' + maxMemSize + ' cpu core id(s):' + bcolors.ENDC)
                            else:
                                print(bcolors.FAIL + '\nYou entered wrong Port number:' + serverPORT + bcolors.ENDC)
                        else:
                            print(bcolors.FAIL + '\nYou entered wrong IP number:' + serverIP + bcolors.ENDC)
                    elif operationType == '2' or operationType == 'del':
                        funcNodesList()
                        delNodeID = input('\nPlease enter node number which you want to delete :')
                        if delNodeID.isdigit():
                            if len(pareNodes) >= int(delNodeID):
                                if delPareNode(delNodeID):
                                    serverIP = pareNodes[int(delNodeID) - 1][0][0]
                                    serverPORT = pareNodes[int(delNodeID) - 1][1][0]
                                    cpuCoreIDs = pareNodes[int(delNodeID) - 1][2][0]
                                    maxMemSize = pareNodes[int(delNodeID) - 1][3][0]
                                    oldVal = "pareNodes.append([['" + serverIP + "'],['" + serverPORT + "'],['" + cpuCoreIDs + "'],['" + maxMemSize + "'],True])"
                                    newVal = "pareNodes.append([['" + serverIP + "'],['" + serverPORT + "'],['" + cpuCoreIDs + "'],['" + maxMemSize + "'],False])"
                                    del pareNodes[int(delNodeID) - 1]
                                    changePareNodeListFile(oldVal, newVal)
                                    try:
                                        sys.exit("To continue run cli again !!! NodeList will be updated") 
                                    except SystemExit as e:
                                        raise SystemExit("\nScript terminated: " + str(e)) 
                                else:
                                    print('!!! Problem occurred  while processing.. !!!\n')
                            else:
                                print('\nYou entered wrong Node number:' + delNodeID)
                        else:
                            print('\nYou entered wrong Node number:' + delNodeID)
                        input('\nPress enter  to continue...')
                    else:
                        print(bcolors.FAIL + '!!!You entered wrong value!!! : ' + operationType + bcolors.ENDC)
                elif returnVAl == "2":  # Move Slot(s)
                    print(bcolors.BOLD + 'Move Slot(s)' + bcolors.ENDC)
                    nodeNumber = 0
                    for pareNode in pareNodes:
                        nodeIP = pareNode[0][0]
                        portNumber = pareNode[1][0]
                        nodeNumber = nodeNumber + 1
                        if pareNode[4]:
                            isPing = pingNode(nodeIP, portNumber)
                            if isPing:
                                slotInfo(nodeIP, portNumber)
                                break
                    fromNodeID = input(bcolors.BOLD + '\nPlease enter FROM node ID :' + bcolors.ENDC)
                    toNodeID = input(bcolors.BOLD + '\nPlease enter TO node ID :' + bcolors.ENDC)
                    numberOfSlots = input(bcolors.BOLD + '\nPlease enter NUMBER of SLOTs :' + bcolors.ENDC)
                    if numberOfSlots.isdigit():
                        if int(numberOfSlots) < 16386:
                            reshardCluster(nodeNumber, fromNodeID, toNodeID, numberOfSlots)
                            returnVAl = input(
                                bcolors.BOLD + "Operation completed. Press enter to continue..." + bcolors.ENDC)
                        else:
                            print(bcolors.FAIL + '!!! This is not valid number value (out of range) !!!' + bcolors.ENDC)
                    else:
                        print(bcolors.FAIL + '!!! This is not valid  value !!!' + bcolors.ENDC)
                elif returnVAl == "3":  # Redis Cluster Nodes Version Upgrade
                    # pmdStatus,cmdResponse = subprocess.getstatusoutput(redisConnectCmd(nodeIP,portNumber,
                    # ' info server | grep  redis_version')) crsRes=cmdResponse.find('redis_version:')
                    # redisVersion=cmdResponse[crsRes]
                    #global redisVersion
                    global redisBinaryDir
                    # global redisTarFile
                    print(bcolors.BOLD + 'Redis Cluster Nodes Version Upgrade' + bcolors.ENDC)
                    newTarFile = input(bcolors.BOLD + "\nPlease Enter new Redis tar file name :" + bcolors.ENDC)
                    newTarFile = newTarFile.lower()
                    serverList = []
                    noProblem = True
                    for pareNode in pareNodes:
                        nodeIP = pareNode[0][0]
                        if pareNode[4]:
                            serverList.append(nodeIP)
                    myServers = list(set(serverList))
                    if (os.path.isfile(newTarFile) and newTarFile[len(newTarFile) - 7:] == '.tar.gz' and (
                            newTarFile[:6]) == 'redis-'):
                        newRedisVersion = newTarFile[6:len(newTarFile) - 7]
                        if newRedisVersion == redisVersion:
                            print(
                                bcolors.WARNING + '!!! New redis version equals to current version !!! Operation '
                                                  'canceled. !!!' + bcolors.ENDC)
                        else:
                            if compileRedis(newTarFile, newRedisVersion):
                                for myServer in myServers:
                                    noProblem = redisNewBinaryCopier(myServer, newRedisVersion)
                                    if not noProblem:
                                        break
                            else:
                                print(bcolors.FAIL + ' :: There is a problem. While compiling redis !!!' + bcolors.ENDC)
                            if noProblem:
                                doRestart = input(
                                    bcolors.OKGREEN + "\nRedis binary copy process completed. Do you want to restart "
                                                      "redis cluster nodes(yes/no)" + bcolors.ENDC)
                                doRestart = doRestart.lower()
                                if doRestart == 'yes':
                                    sRisOK = restartAllSlaves(newRedisVersion)
                                    if sRisOK:
                                        mRisOK = restartAllMasters(newRedisVersion)
                                        if not mRisOK:
                                            myRes = input(
                                                bcolors.BOLD + "\nDo you want to try again until all master nodes "
                                                               "return OK (yes/no):" + bcolors.ENDC)
                                            myRes.lower()
                                            if myRes == 'yes':
                                                while not restartAllMasters(newRedisVersion):
                                                    print(
                                                        bcolors.BOLD + 'The Operation will be tried again, 1 minute '
                                                                       'later. Please wait .. ' + bcolors.ENDC)
                                                    sleep(60)
                                                redisBinaryDir = redisBinaryDir.replace('redis-' + redisVersion,
                                                                                        'redis-' + newRedisVersion)
                                                if (changePareConfigFile("redisVersion = '" + redisVersion + "'",
                                                                         "redisVersion = '" + newRedisVersion + "'") and changePareConfigFile(
                                                    "redisTarFile = 'redis-" + redisVersion + ".tar.gz'",
                                                    "redisTarFile = 'redis-" + newRedisVersion + ".tar.gz'")):
                                                    print(
                                                        bcolors.OKGREEN + ':: Redis version was changed and '
                                                                          'pareConfig File was updated !!!' +
                                                        bcolors.ENDC)
                                                    nodeNumber = 0
                                                    redisVersion = newRedisVersion
                                                    for pareNode in pareNodes:
                                                        nodeIP = pareNode[0][0]
                                                        portNumber = pareNode[1][0]
                                                        nodeNumber = nodeNumber + 1
                                                        if pareNode[4]:
                                                            print(bcolors.BOLD + 'Node Number :' + str(
                                                                nodeNumber) + '  Node IP :' + nodeIP + '  Node Port :' + portNumber + bcolors.ENDC)
                                                            os.system(redisConnectCmd(nodeIP, portNumber,
                                                                                      'info server | grep'
                                                                                      'redis_version'))
                                                else:
                                                    print(
                                                        bcolors.FAIL + ':: There is a problem. While changing'
                                                                       'pareConfig File !!!' + bcolors.ENDC)
                                        else:
                                            redisBinaryDir = redisBinaryDir.replace('redis-' + redisVersion,
                                                                                    'redis-' + newRedisVersion)
                                            if (changePareConfigFile("redisVersion = '" + redisVersion + "'",
                                                                     "redisVersion = '" + newRedisVersion + "'") and changePareConfigFile(
                                                "redisTarFile = 'redis-" + redisVersion + ".tar.gz'",
                                                "redisTarFile = 'redis-" + newRedisVersion + ".tar.gz'")):
                                                print(
                                                    bcolors.OKGREEN + ':: Redis version was changed and pareConfig '
                                                                      'File was updated !!!' + bcolors.ENDC)
                                                nodeNumber = 0
                                                redisVersion = newRedisVersion
                                                for pareNode in pareNodes:
                                                    nodeIP = pareNode[0][0]
                                                    portNumber = pareNode[1][0]
                                                    nodeNumber = nodeNumber + 1
                                                    if pareNode[4]:
                                                        print(bcolors.BOLD + 'Node Number :' + str(
                                                            nodeNumber) + '  Node IP :' + nodeIP + '  Node Port :' + portNumber + bcolors.ENDC)
                                                        os.system(redisConnectCmd(nodeIP, portNumber,
                                                                                  ' info server | grep  redis_version'))
                                            else:
                                                print(
                                                    bcolors.FAIL + ':: There is a problem. While changing pareConfig '
                                                                   'File !!!' + bcolors.ENDC)
                                    else:
                                        print(
                                            bcolors.FAIL + ' :: There is a problem. While restarting slave nodes. !!!' + bcolors.ENDC)
                                elif doRestart == 'no':
                                    print(
                                        bcolors.FAIL + "The process will end without Restart. You should do manuel "
                                                       "restart." + bcolors.ENDC)
                                else:
                                    print(bcolors.FAIL + '!!!You entered wrong value!!! : ' + doRestart + bcolors.ENDC)
                    else:
                        print(
                            bcolors.FAIL + '!!! You entered wrong file name!!!\n It must be like "redis-***.tar.gz"' + bcolors.ENDC)
                    sleep(3)
                elif returnVAl == "4":  # Redis Cluster Nodes Version Control
                    print(bcolors.BOLD + 'Redis Cluster Nodes Version Control' + bcolors.ENDC)
                    redisNodesVersionControl()
                    returnVAl = input(bcolors.BOLD + "Press enter to continue..." + bcolors.ENDC)
                    sleep(3)
                elif returnVAl == "5":  # Maintain Server
                    print(bcolors.BOLD + 'Maintain Server\n------------------\n' + bcolors.ENDC)
                    funcNodesList()
                    print(
                        bcolors.WARNING + '!!! BE CAREFULL !!! Depend of your configuration, this process might cause '
                                          'cluster status  FAIL !!!')
                    myServerIP = input(bcolors.BOLD + "\nPlease Enter Server IP : " + bcolors.ENDC)
                    print('Your choise :' + myServerIP)
                    if validIP(myServerIP):
                        nodeNumber = 0
                        for pareNode in pareNodes:
                            nodeIP = pareNode[0][0]
                            if nodeIP == myServerIP and pareNode[4]:
                                portNumber = pareNode[1][0]
                                nodeNumber = nodeNumber + 1
                                stopNode(nodeIP, str(myServerIP), portNumber)
                    else:
                        print(bcolors.FAIL + '!!!You entered wrong IP!!! : ' + myNodeNum + bcolors.ENDC)
                elif returnVAl == "6":  # Migrate data From
                    print(
                        bcolors.WARNING + '!!! This process will migrate whole data from target non-Clustered redis '
                                          'server !!!' + bcolors.ENDC)
                    fromIP = input(bcolors.BOLD + "\nPlease Enter target redis IP address :" + bcolors.ENDC)
                    if validIP(fromIP):
                        fromPORT = input(bcolors.BOLD + "\nPlease Enter target redis port number :" + bcolors.ENDC)
                        fromPWD = input(
                            bcolors.BOLD + "\nPlease Enter target redis password ( If No password, press enter ) :" + bcolors.ENDC)
                        if fromPORT.isdigit():
                            # targetPWD=input("\nPlease Enter target redis password :")
                            nodeNumber = 0
                            for pareNode in pareNodes:
                                nodeIP = pareNode[0][0]
                                portNumber = pareNode[1][0]
                                nodeNumber = nodeNumber + 1
                                if pareNode[4]:
                                    if isNodeMaster(nodeIP, nodeNumber, portNumber):
                                        break
                            toIP = pareNodes[nodeNumber - 1][0][0]
                            toPort = pareNodes[nodeNumber - 1][1][0]
                            print(bcolors.BOLD + 'Migrating process is starting... ' + bcolors.ENDC)
                            # os.system('date')
                            migrateDataFrom(toIP, toPort, fromIP, fromPORT, fromPWD)
                            # os.system('date')
                            input(
                                bcolors.OKGREEN + "\n Migration completed. \n Press Enter to continue..." + bcolors.ENDC)
                        else:
                            print(bcolors.FAIL + '!!! This is not valid port number !!!' + bcolors.ENDC)
                    else:
                        print(bcolors.FAIL + '!!! This is not valid IP address !!!' + bcolors.ENDC)
                    sleep(3)
                elif returnVAl == "7":  # Cluster Load(Slots) Balancer
                    print(bcolors.BOLD + 'Cluster Slot(load) Balancer' + bcolors.ENDC)
                    balanceSt = input(
                        bcolors.BOLD + "Please select balance Strategy\n1 - node base\n2 - memory size base \n :" + bcolors.ENDC)
                    balanceStrategy = ''
                    if balanceSt == '1':
                        balanceStrategy = 'nodeBase'
                        maxSlotBarier = input(
                            bcolors.BOLD + "\nPlease Enter max move slot Number per Node ( between 0 - 4000 )(0 means "
                                           "no limit):" + bcolors.ENDC)
                        if maxSlotBarier.isdigit():
                            if int(maxSlotBarier) < 4001:
                                clusterSlotBalanceMapper(balanceStrategy, int(maxSlotBarier))
                            else:
                                print(bcolors.FAIL + '\n!!! You  entered wrong value !!!' + bcolors.ENDC)
                        else:
                            print(bcolors.FAIL + '\n!!! You  entered wrong value !!!' + bcolors.ENDC)
                    elif balanceSt == '2':
                        balanceStrategy = 'memBase'
                        maxSlotBarier = input(
                            bcolors.BOLD + "\nPlease Enter max move slot Number ( between 0 - 4000 )(0 means no limit):" + bcolors.ENDC)
                        if maxSlotBarier.isdigit():
                            if int(maxSlotBarier) < 4001:
                                clusterSlotBalanceMapper(balanceStrategy, int(maxSlotBarier))
                            else:
                                print(bcolors.FAIL + '\n!!! You  entered wrong value !!!' + bcolors.ENDC)
                        else:
                            print(bcolors.FAIL + '\n!!! You  entered wrong value !!!' + bcolors.ENDC)

                    else:
                        print(bcolors.FAIL + '\n!!! You  entered wrong choice !!!' + bcolors.ENDC)
                elif returnVAl == "8":  # Not Designated
                    print("hello man")
                elif returnVAl == "9":  # Main Menu
                    print(
                        bcolors.BOLD + "your Choise :" + returnVAl + " --- You are going to Main Menu ..." + bcolors.ENDC)
                    MenuState = 0
                elif returnVAl == "10":  # Exit
                    print("your Choise : " + bcolors.BOLD + returnVAl + bcolors.ENDC)
                    print("\n Goodbye")
                    exit()
                else:
                    print(bcolors.WARNING + "\n !!! Not Valid Choice! Try again" + bcolors.ENDC)
                    sleep(1)
            sleep(1)
        elif ans == "4":
            MenuState = 0
            if os.path.isfile('paredicma.done'):
                resCluster = input(
                    bcolors.WARNING + "\nRedis cluster is already done. You DO NOT remake cluster. (for force make "
                                      "remove 'paredicma.done' file)" + bcolors.ENDC)
                resCluster = resCluster.lower()
            else:
                resCluster = input(bcolors.BOLD + " Are you sure to make Redis Cluster (yes/no) ? " + bcolors.ENDC)
                if resCluster == 'yes':
                    redisReplicationNumber = input(
                        bcolors.BOLD + "How many replica( slave ) do you want for each master ('0','1','2' ext.) ? " + bcolors.ENDC)
                    if redisReplicationNumber.isdigit():
                        if (int(redisReplicationNumber) * 3) <= len(pareNodes):
                            pareClusterMaker(redisReplicationNumber)
                            returnVAl = input(bcolors.BOLD + "Press enter to continue..." + bcolors.ENDC)
                        else:
                            print(
                                bcolors.FAIL + "!!! You do NOT have enough nodes to setup this configuration !!!\n "
                                               "please check replication number and pareNodes.py file !!!!" +
                                bcolors.ENDC)
                    else:
                        print(bcolors.FAIL + '!!! You entered wrong value !!!!' + bcolors.ENDC)
                    # os.system('python paredicma.py')
                    print(bcolors.OKGREEN + 'WELL DONE ;)' + bcolors.ENDC)
            menuMain()
        elif ans == "5":
            print("\n Goodbye")
            exit()
        else:
            print(bcolors.WARNING + "\n !!! Not Valid Choice! Try again" + bcolors.ENDC)


main()
