# !/usr/bin/python
  
from pareNodeList import *

projectName = 'releaseTest'+'Cache'
pareOSUser = 'alper'
pareWebPort = 8000
redisDataDir = '/data/'+pareOSUser+'/projects/'+projectName+'/'
redisConfigDir = '/data/'+pareOSUser+'/projects/'+projectName+'/conf/'
redisLogDir = '/data/'+pareOSUser+'/projects/'+projectName+'/log/'
redisVersion = '7.4.2'
redisTarFile = 'redis-7.4.2.tar.gz'
redisBinaryDir = '/data/'+pareOSUser+'/reBin/redis-'+redisVersion+'/'
redisBinaryBase = '/data/'+pareOSUser+'/reBin/'
dedicateCore = True   # True/False
doCompile = True
doStartNodes = True
unixSocketDir = '/tmp/'
pidFileDir = '/var/run/'
writePareLogFile = True
pareLogFile = ''+projectName+'.log'
pareTmpDir = 'temparedicma/'
pareServerIp = '127.0.0.1'  # paredicma console server
rdb = 'on'   # on/off if not needed turn off after creating cluster.  
# dbfilename "dumpN1_P9773.rdb"
rdbValue = 'save 3600 1000\nsave 1800 10000\nsave 600 100000'
aof = 'on'   # on/off  if not needed turn off after creating cluster.
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

#### Config File was Changed by paredicma at 2025.05.04 15:01:35
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:01:35
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:02:50
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:02:50
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:06:17
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:06:17
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:06:21
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:06:21
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:06:42
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:06:42
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:06:44
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:06:44
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:06:45
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:06:45
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:06:46
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:06:46
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:10:12
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:10:12
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:13:34
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:13:34
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:21:36
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:21:36
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:24:03
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:24:03
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:25:28
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:25:28
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:29:21
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:29:21
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:37:58
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:37:58
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:40:19
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:40:19
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:46:14
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:46:14
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:47:47
#### old value:redisVersion = '7.4.2'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:47:47
#### old value:redisTarFile = 'redis-7.4.2.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'

#### Config File was Changed by paredicma at 2025.05.04 15:54:25
#### old value:redisVersion = '7.4.1'
#### new value:redisVersion = '7.4.2'

#### Config File was Changed by paredicma at 2025.05.04 15:54:25
#### old value:redisTarFile = 'redis-7.4.1.tar.gz'
#### new value:redisTarFile = 'redis-7.4.2.tar.gz'
