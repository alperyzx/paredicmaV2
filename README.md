# Python Automatic REDIs Cluster MAnager & MAker
#### Author				: Mustafa YAVUZ
#### E-mail				: msyavuz@gmail.com, paredicma@gmail.com

## Version: 2.0 
#### UpdateDate				: 07.12.2023
#### UpdatedBy				: ALPER YILDIZ (a.alper.yildiz@gmail.com) 
#### Release Note			: Python3 support
#### Software Requirement	: Python3.x or above, sshd( with passwordless ssh-keygen auth. between servers ), numactl 
#### OS System 				: Redhat/Centos 7+ ( possible Ubuntu, debian )

## Version: 2.1
#### UpdateDate				: 27.02.2024
#### UpdatedBy				: ALPER YILDIZ (a.alper.yildiz@gmail.com) 
#### Release Note			: Web View Support with FastAPI (Monitoring Section)

## Version: 2.5
#### UpdateDate				: 05.05.2025
#### UpdatedBy				: ALPER YILDIZ (a.alper.yildiz@gmail.com) 
#### Release Note			: Enhanced Management and Maintenance features, including Redis Cluster Upgrade.

## Python Automatic REDIs Cluster MAnager&MAker
This program is developed by Mustafa YAVUZ (msyavuz@gmail.com) to make Redis Cluster installation, managament, upgrade and maintanence easier, especially for non-Docker environments.
It includes current redis tar file. If You have, you can try paredicma with newer version redis, with changing redis tar file.

## Prerequirements:
sshd ( with passwordless ssh-keygen auth. between servers ),
numactl( if you want to use dedicate cpu-core )

cli: python 3.1,
webview: python 3.8, fastapi, uvicorn

## 1- Download and extract :
Download -> paredicmaV2-master.zip
extract -> unzip paredicmaV2-master.zip
cd paredicmaV2-master

## 2- Installation :
You do not need to install it, Just configure and run it.

## 3- Configuration :
Configure pareNodeList.py file, change ip, port, cpu core and max_memory per node, according to your cluster.
Configure pareConfig.py file, according to your cluster

## 4 - run program
cli: python3.x paredicma-cli.py
webview: python3.x parewebMon.py

## 5- enjoy it :)

		PAREDICMA CLI (Python Automatic REDIs Cluster MAker)
        ------------------------------------------------
        1 - Redis Cluster Monitor - ( paredicmon ) 
        2 - Redis Cluster Manager - ( paredicman ) 
        3 - Redis Cluster Upgrade&Migration&Maintenance - ( paredicmum ) 
        4 - Redis Cluster Maker - ( paredicma  ) 
        5 - Exit                                                                                                        

        ------------------------------------------------
        What would you like to do? 

or If you have already made a cluster		
		
        PAREDICMA CLI (Python Automatic REDIs Cluster MAker)                
        ------------------------------------------------
        1 - Redis Cluster Monitor - ( paredicmon ) 
        2 - Redis Cluster Manager - ( paredicman ) 
        3 - Redis Cluster Upgrade & Migration & Maintenance - ( paredicmum ) 
        NAP - Redis Cluster Maker - Already Done - ( paredicma  ) 
        5 - Exit                                                                                   

        ------------------------------------------------
        What would you like to do? 

If you choose #1		
		
        PAREDICMON - REDIS CLUSTER MONITOR
        ------------------------------------------------
          1 - Ping  Node(s)             
          2 - List Nodes        
          3 - node(s) Info     
          4 - Server Info            
          5 - Slots Info                
          6 - Cluster State             
          7 - Show Memory Usage         
          8 - Not Designated            
          9 - Main Menu                 
         10 - Exit                      

        ------------------------------------------------
        What would you like to do? :

If you choose #2		
		
		PAREDICMAN - REDIS CLUSTER MANAGER
        ------------------------------------------------
          1 - Start/Stop/Restart Redis Node     
          2 - Switch Master/Slave Nodes
          3 - Change Redis Configuration Parameter
          4 - Save Redis Configuration to redis.conf  
          5 - Rolling Restart                       
          6 - Command for all nodes                         
          7 - Show Redis Log File           
          8 - Not Designated            
          9 - Main Menu                 
         10 - Exit                      

        ------------------------------------------------
        What would you like to do? :
		
If you choose #3
		
		PAREDICMUM - REDIS CLUSTER MIGRATION&UPGRADE&MAINTENANCE
        ------------------------------------------------
          1 - Add/Delete Redis Node        
          2 - Move Slot(s)       
          3 - Redis Cluster Nodes Version Upgrade 
          4 - Redis Cluster Nodes Version Control
          5 - Maintain Server                               
          6 - Migrate Data From Remote Redis
          7 - Cluster Slot(load) Balancer                           
          8 - Not Designated                                                
          9 - Main Menu                 
         10 - Exit                      

        ------------------------------------------------
		What would you like to do? 
		
If you choose #4
		
		        PAREDICMA CLI (Python Automatic REDIs Cluster MAker)
        ------------------------------------------------
        1 - Redis Cluster Monitor - ( paredicmon ) 
        2 - Redis Cluster Manager - ( paredicman ) 
        3 - Redis Cluster Upgrade&Migration&Maintenance - ( paredicmum ) 
        4 - Redis Cluster Maker - ( paredicma  ) 
        5 - Exit                                                                                                        

        ------------------------------------------------
        What would you like to do? 4
        Are you sure to make Redis Cluster (yes/no) ? 



© 2023 GitHub, Inc.
