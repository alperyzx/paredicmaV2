# !/usr/bin/python

import os
import subprocess
import sys
from time import sleep
# from pareConfig import *
from pareFunc import *
from screenMenu import *
from paredicma import *


def main():
    os.system("clear")
    while True:
        nodeNumber = 0
        totalUsedMemByte = 0
        totalMaxMemByte = 0
        printTextMaster = ''
        printTextSlave = ''
        totalMemPer = 0.0

        for pareNode in pareNodes:
            nodeIP = pareNode[0][0]
            portNumber = pareNode[1][0]
            nodeNumber += 1

            if pareNode[4]:
                memStatus, memResponse = subprocess.getstatusoutput(
                    redisConnectCmd(nodeIP, portNumber, ' info memory | grep  -e "used_memory:" -e "maxmemory:" '))

                if memStatus == 0:
                    usedMemByte = float(memResponse[12:memResponse.find('maxmemory:') - 1])
                    maxMemByte = float(memResponse[memResponse.find('maxmemory:') + 10:])
                    usedMem = round(usedMemByte / (1024 * 1024 * 1024), 3)
                    maxMem = round(maxMemByte / (1024 * 1024 * 1024), 3)
                    usagePerMem = round((usedMem / maxMem) * 100, 2)

                    if isNodeMaster(nodeIP, nodeNumber, portNumber):
                        totalUsedMemByte += usedMemByte
                        totalMaxMemByte += maxMemByte
                        printTextMaster += bcolors.OKGREEN + str(
                            nodeNumber) + '\t' + nodeIP + '-( M )\t' + portNumber + '\t' + str(usedMem) + '\t' + str(
                            maxMem) + '\t' + str(usagePerMem) + '%' + bcolors.ENDC + '\n'
                    else:
                        printTextSlave += bcolors.OKGREEN + str(
                            nodeNumber) + '\t' + nodeIP + '-( S )\t' + portNumber + '\t' + str(usedMem) + '\t' + str(
                            maxMem) + '\t' + str(usagePerMem) + '%' + bcolors.ENDC + '\n'

                    if usagePerMem >= 90.0:
                        if isNodeMaster(nodeIP, nodeNumber, portNumber):
                            printTextMaster += bcolors.FAIL + str(
                                nodeNumber) + '\t' + nodeIP + '-( M )\t' + portNumber + '\t' + str(
                                usedMem) + '\t' + str(maxMem) + '\t' + str(usagePerMem) + '%' + bcolors.ENDC + '\n'
                        else:
                            printTextSlave += bcolors.FAIL + str(
                                nodeNumber) + '\t' + nodeIP + '-( S )\t' + portNumber + '\t' + str(
                                usedMem) + '\t' + str(maxMem) + '\t' + str(usagePerMem) + '%' + bcolors.ENDC + '\n'

                    elif 80.00 <= usagePerMem < 90.00:
                        if isNodeMaster(nodeIP, nodeNumber, portNumber):
                            printTextMaster += bcolors.WARNING + str(
                                nodeNumber) + '\t' + nodeIP + '-( M )\t' + portNumber + '\t' + str(
                                usedMem) + '\t' + str(maxMem) + '\t' + str(usagePerMem) + '%' + bcolors.ENDC + '\n'
                        else:
                            printTextSlave += bcolors.WARNING + str(
                                nodeNumber) + '\t' + nodeIP + '-( S )\t' + portNumber + '\t' + str(
                                usedMem) + '\t' + str(maxMem) + '\t' + str(usagePerMem) + '%' + bcolors.ENDC + '\n'

                    else:
                        if isNodeMaster(nodeIP, nodeNumber, portNumber):
                            printTextMaster += bcolors.OKGREEN + str(
                                nodeNumber) + '\t' + nodeIP + '-( M )\t' + portNumber + '\t' + str(
                                usedMem) + '\t' + str(maxMem) + '\t' + str(usagePerMem) + '%' + bcolors.ENDC + '\n'
                        else:
                            printTextSlave += bcolors.OKGREEN + str(
                                nodeNumber) + '\t' + nodeIP + '-( S )\t' + portNumber + '\t' + str(
                                usedMem) + '\t' + str(maxMem) + '\t' + str(usagePerMem) + '%' + bcolors.ENDC + '\n'

                else:
                    print(
                        bcolors.FAIL + '!!! Warning !!!! A problem occurred, while memory usage checking !!! nodeID :'
                        + str(nodeNumber) + ' NodeIP:' + nodeIP + ' NodePort:' + portNumber + '' + bcolors.ENDC)

        os.system("clear")
        print(
            bcolors.HEADER + projectName + ' Redis Cluster  Memory Usage'
            + bcolors.ENDC + ' ( ' + get_datetime() + ')\n----------------')
        print(
            bcolors.HEADER + 'nodeID\tNodeIP\t\t\tNodePort\tUsed Mem(GB)\tMax Mem(GB)\tUsage Percentage(%)'
            + bcolors.ENDC)
        print(
            printTextMaster + bcolors.BOLD + '--------------------------------------' + bcolors.ENDC)
        print(printTextSlave)
        totalUsedMem = round((totalUsedMemByte / (1024 * 1024 * 1024)), 3)
        totalMaxMem = round((totalMaxMemByte / (1024 * 1024 * 1024)), 3)

        if totalMaxMem == 0:
            totalMemPer = 0.0
        else:
            totalMemPer = round(((totalUsedMem / totalMaxMem) * 100), 2)

        print(
            bcolors.BOLD + '--------------------------------------' + bcolors.ENDC)
        print(bcolors.BOLD + 'TOTAL( Only Master )\t\t\t\t\t:' + str(totalUsedMem) + 'GB\t' + str(
            totalMaxMem) + 'GB\t\t' + str(totalMemPer) + '% ' + bcolors.ENDC)
        sleep(10)


if __name__ == "__main__":
    main()
