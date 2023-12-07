#!/usr/bin/python

import os
import sys
from time import *
from pareConfig import *
from pareFunc import *


# def main():
def pareClusterMaker(redisReplicationNumber):
    nodeNumber = 0
    serverList = []
    makeDir(pareTmpDir)
    for pareNode in pareNodes:
        slaveOfWhom = ''
        nodeIP = pareNode[0][0]
        portNumber = pareNode[1][0]
        dedicateCpuCores = pareNode[2][0]
        maxMemorySize = pareNode[3][0]
        nodeNumber = nodeNumber + 1
        if pareNode[4]:
            serverList.append(nodeIP)
            redisDirMaker(nodeIP, str(nodeNumber))
            redisConfMaker(nodeIP, str(nodeNumber), portNumber, maxMemorySize)
    myServers = list(set(serverList))
    if doCompile:
        redisTarFileName = redisTarFile
        redisCurrentVersion = redisVersion
        if compileRedis(redisTarFileName, redisCurrentVersion):
            for myServer in myServers:
                redisBinaryCopier(myServer, redisVersion)
        else:
            logWrite(pareLogFile, ' :: There is a problem. While compiling redis!!!')
    if doStartNodes:
        nodeNumber = 0
        for pareNode in pareNodes:
            nodeIP = pareNode[0][0]
            portNumber = pareNode[1][0]
            dedicateCpuCores = pareNode[2][0]
            nodeNumber = nodeNumber + 1
            if pareNode[4]:
                startNode(nodeIP, str(nodeNumber), portNumber, dedicateCpuCores)
    if redisCluster == 'on':
        nodesString = ''
        slaveNodes = []
        for pareNode in pareNodes:
            nodeIP = pareNode[0][0]
            portNumber = pareNode[1][0]
            if pareNode[4]:
                nodesString += ' ' + nodeIP + ':' + portNumber
        makeRedisCluster(nodesString, redisReplicationNumber)
    os.system('touch paredicma.done')
# main()
