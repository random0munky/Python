#!/usr/bin/python

# This script's purpose is to pull the named.stats from FirstNet servers

import subprocess
import socket

SERVER_LIST = "/appl/node_exporter/scripts/named.server_list"
MECHID = "m29800"
PRIV_KEY = "/appl/node_exporter/scripts/m29800_key"
REMOTE_STATS = "/usr/local/dns/stats/named.stats"
DEST_STATS = "/appl/node_exporter/stats/original/named.stats"
PROM_DIR = "/appl/node_exporter/stats/prom"


# This function is used to open, read and add the servers into an array. Ignoring servers that are commented out with '#'
def server_list():
	server_list = open(SERVER_LIST, "r")
	read_servers = server_list.readlines()
	
	server_array = []
	for server in read_servers:
		server = server.replace('\n','')
		if not server.startswith('#') and server != '':
			server_array.append(server)
	
	return server_array

# This function is used to scp the named.stats file from the passed server
# Named.stats file will have "_{hostname}" appended to it.
def scp(ip, server):
	dest_stats = "%s_%s" %(DEST_STATS, server)
	command = "/usr/bin/scp -q -i %s -o 'BatchMode yes' -o 'StrictHostKeyChecking=no' %s@%s:%s %s" %(PRIV_KEY, MECHID, ip, REMOTE_STATS, dest_stats)
	subprocess.call([command], shell=True)

# This function is used to find the short hostname of the IP address of the server being passed
def nslookup(ip):
	fqdn = socket.gethostbyaddr(ip)[0]
	short = fqdn.split('.')[0]
	return short

# This function is used to open the permissions of the prom directory file contents so node_exporter can read them
def permissions():
	command = "/bin/chmod -R o+r %s" %(PROM_DIR)
	subprocess.call([command], shell=True)
	
# Main function
# 1st step is to scp the named.stats file of the passed server
# 2nd step is to call the parser script, passing the server being used. Using sys.argv to pass server variable when calling the parser script.
def main():
	ips = server_list()
	for ip in ips:
		server = nslookup(ip)
		scp(ip, server)
		command = "/usr/bin/python /appl/node_exporter/scripts/named.stats.parser.py %s" % (server)
		subprocess.call([command], shell=True)
	permissions()
	
main()
