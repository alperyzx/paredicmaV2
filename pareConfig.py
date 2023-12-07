# !/usr/bin/python

from pareNodeList import *

projectName = 'redis11'+'Cache'
redisDataDir = '/data/redisuser/projects/'+projectName+'/'
redisConfigDir = '/data/redisuser/projects/'+projectName+'/conf/'
redisLogDir = '/data/redisuser/projects/'+projectName+'/log/'
redisVersion = '7.2.3'
redisTarFile = 'redis-7.2.3.tar.gz'
redisBinaryDir = '/data/redisuser/reBin/redis-'+redisVersion+'/'
dedicateCore = False   # True/False
doCompile = True
doStartNodes = True
unixSocketDir = '/tmp/'
pidFileDir = '/var/run/'
writePareLogFile = True
pareLogFile = ''+projectName+'.log'
pareTmpDir = 'temparedicma/'
pareServerIp = '192.168.1.5'  # paredicma console server
pareOSUser = 'redisuser'
rdb = 'on'   # on/off
# dbfilename "dumpN1_P9773.rdb"
rdbValue = 'save 3600 1000\nsave 1800 10000\nsave 600 100000'
aof = 'on'   # on/off
# appendfilename "appendonlyN1_P9773.aof"
aofValue = 'appendfsync everysec'
redisCluster = 'on'   # on/off
clusterNodeTimeout = 'cluster-node-timeout 5000'
clusterParameters = 'cluster-replica-validity-factor 0\ncluster-migration-barrier 1'
maxMemory = 'on'   # on/off
redisPwdAuthentication = 'on'   # on/off
redisPwd = 'u3**x5**sRE'
redisParameters = '''
daemonize yes
slowlog-log-slower-than 1000
latency-monitor-threshold 100
slowlog-max-len 10
rename-command FLUSHALL "aO**3p**qw"
rename-command FLUSHDB  "qw**f0**tU"
'''