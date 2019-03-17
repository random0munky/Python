#!/usr/bin/python

# Features. Have an argument to specify time frames
# No period on printed output


# This Python script is a reporting tool to compute the QPS with given parameters such as time frames

import os
import sys
import sqlite3
import subprocess
import re
import time

NAMED_LOCATION = "/usr/local/dns/stats/named.stats"
DATABASE_FILE = "named_report.db"
RNDC = "/opt/isc/sbin/rndc"
QPS_SLEEP = "10"

def copy_named_stats():
	# Get python script directory to copy the named.stats file to
	script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
	command = "/usr/bin/cp %s %s/named.stats.copy" %(NAMED_LOCATION, script_dir)
	subprocess.call([command], shell=True)
	return script_dir

def execute_rndc():
	command = "%s stats" %(RNDC)
	subprocess.call([command], shell=True)
	
def create_db():
	# Create DB
	conn = sqlite3.connect('named_stats_report.db')
	# To perform SQL commands, create a Cursor object
	c = conn.cursor()
	# Drop tables incoming_requests,incoming_queries,
	# outgoing_queries,ns_stats,resolver_stats if it already exists
	c.execute('''DROP TABLE IF EXISTS incoming_requests''')
	c.execute('''DROP TABLE IF EXISTS ns_stats''')
	conn.commit()
	# The execute method allows the ability to perform SQL commands
	# Create Table incoming_requests,incoming_queries,\
	# outgoing_queries,ns_stats,resolver_stats
	# Columns: time, inc_queries
	c.execute('''CREATE TABLE incoming_requests(
					time int primary key,
					inc_queries int)''')
	c.execute('''CREATE TABLE ns_stats(
					time int primary key,
					successful int)''')
	conn.commit()
	return c, conn

# This function is to read the named.stats.copy to output formatted named.stats file
# This outputs the last statistics dump for named.stats
def output_formatted_stats(script_dir):
	stats_file = "%s/named.stats.copy" %(script_dir)
	stats_copy = open(stats_file, "r")
	stats_contents = stats_copy.readlines()
	# Gets the last line of the file and strips any carriage returns/new lines
	stats_lastline = stats_contents[-1].strip()
	# Get the epoch time of the stats dump
	stats_epochtime = re.search('\(([^)]+)', stats_lastline).group(1).strip()
	# Now that we have the epochtime, we need to get the line numbers where the epoch time exists
	# epoch_line array contains the start and end line numbers
	epoch_line = []
	formatted_stats = "%s/named.stats.formatted" %(script_dir)
	format_stats = open(formatted_stats, "w")
	for num, line in enumerate(stats_contents, 1):
		if stats_epochtime in line:
			#print "Found epochtime at this line number: %s" %(num)
			epoch_line.append(num)

	# This for loop takes the two epoch array values (had to -1 for the starting value because it was getting left out)
	# Which then writes the line contents from the range between the two values to a 2nd file.
	for line in range((epoch_line[0] - 1), epoch_line[1]):
		format_stats.write(stats_contents[line])
	
	return formatted_stats, stats_epochtime

# This function is to take the formatted named.stats file, parse through the file given line number ranges
# Save each of the section's values inside the named.stats file, into arrays. Return arrays.
# Outputting a tuple array which contains: (stat_value, stat name)
# This way, the statistics are "flexible" in the sense of logging all types of traffic. No traffic shall be left out.
def formatted_iteration(c, conn, stats_epochtime, formatted_file):
	new_stats = open(formatted_file, "r")
	new_content = new_stats.readlines()
	
	inc_req_line = []
	inc_query_line = []
	out_rcodes_line = []
	out_query_line = []
	ns_query_line = []
	resolver_line = []
	cache_line = []
	
	# Lets look for lines that start with a "++".
	# Get the line numbers for each of the sections; they start with a "++"
	for num, line in enumerate(new_content, 1):
		if line.startswith("++ Incoming Requests"):
			inc_req_line.append(num)
		elif line.startswith("++ Incoming Queries"):
			inc_query_line.append(num)
		elif line.startswith("++ Outgoing Rcodes"):
			out_rcodes_line.append(num)
		elif line.startswith("++ Outgoing Queries"):
			out_query_line.append(num)
		elif line.startswith("++ Name Server Statistics"):
			ns_query_line.append(num)
		elif line.startswith("++ Resolver Statistics"):
			resolver_line.append(num)
		elif line.startswith("++ Cache Statistics"):
			cache_line.append(num)
			
	# Index for which array I'm looping through for adding values to.
	array_index = 0
	# For loops to go through each section of the named.stats file
	#Incoming Requests: QUERY, etc.
	incoming_requests = []
	for line in range(inc_req_line[0], (inc_query_line[0] - 1)):
		inc_request = new_content[line].strip()
		inc_req_value = inc_request.split(' ', 1)[0]
		inc_stat = inc_request.split(' ', 1)[1]
		inc_stat = check_stat(inc_stat)
		check_name(c, conn, stats_epochtime, inc_stat, inc_req_value)
	#print "Incoming Requests: %s" %(incoming_requests)
	
	# Incoming Queries: A, PTR, AAAA, NAPTR, ANY, etc.
	incoming_queries = []
	for line in range(inc_query_line[0], (out_rcodes_line[0] - 1)):
		inc_query = new_content[line].strip()
		inc_query_value = inc_query.split(' ', 1)[0]
		query_stat = inc_query.split(' ',1)[1]
		inc_query_stat = check_stat(query_stat)
	#print "Incoming Queries: %s" %(incoming_queries)
	
	# Outgoing Rcodes: NOERROR, SERVFAIL, NXDOMAIN
	outgoing_rcodes = []
	for line in range(out_rcodes_line[0], (out_query_line[0] -1)):
		rcode_query = new_content[line].strip()
		rcode_query_value = rcode_query.split(' ', 1)[0]
		query_stat = rcode_query.split(' ',1)[1]
		rcode_query_stat = check_stat(query_stat)
	#print "Outgoing Rcodes: %s" %(outgoing_rcodes)
	
	
	# Outgoing Queries: A, PTR, AAAA, NAPTR, ANY, etc
	outgoing_queries = []
	for line in range(out_query_line[0], (ns_query_line[0] - 1)):
		out_query = new_content[line].strip()
		out_query_value = out_query.split(' ', 1)[0]
		query_stat = out_query.split(' ',1)[1]
		out_query_stat = check_stat(query_stat)
	#print "Outgoing Queries: %s" %(outgoing_queries)
	
	# Name Server Statistics: IPv4 requests received, requests with EDNS(0) received, TCP requests received, responses sent, truncated responses sent, responses with EDNS(0) sent, queries resulted in successful answer, queries resulted in authoritative answer, queries resulted in non authoritative answer, queries resulted in nxrrset, queries resulted in SERVFAIL, queries resulted in NXDOMAIN, queries caused recursion, queries dropped, UDP queries received, TCP queries received
	ns_stats = []
	for line in range(ns_query_line[0], (resolver_line[0] - 1)):
		ns_stat = new_content[line].strip()
		ns_value = ns_stat.split(' ', 1)[0]
		ns_stat = ns_stat.split(' ',1)[1]
		ns_stat = check_stat(ns_stat)
		check_name(c, conn, stats_epochtime, ns_stat, ns_value)
	#print "Name Server Stats: %s" %(ns_stats)
	
	#Resolver Statistics: IPv4 queries sent, IPv4 responses received, NXDOMAIN received, SERVFAIL received, truncated responses received, lame delegations received, query retries, query timeouts, IPv4 NS address fetches, IPv6 NS address fetches, IPv4 NS address fetch failed, IPv6 NS address fetch failed, queries with RTT < 10ms, queries with RTT 10-100ms, queries with RTT 100-500ms, queries with RTT 500-800ms, queries with RTT 800-1600ms, bucket size, SIT sent client cookie only
	# Had to skip an array value to be in the Resolver Statistics section of the file.
	resolver_stats = []
	# for line in range(resolver_line[0], (cache_line[0] - 1)):
		# resolver_stat = new_content[line].strip()
		# resolver_value = resolver_stat.split(' ', 1)[0]
		# resolver_stat = resolver_stat.split(' ',1)[1]
		# resolver_stat = check_stat(resolver_stat)
	# print "Resolver Stats: %s" %(resolver_stats)
	
	# Return
	return

# This function makes the metric name "suitable" for node_exporter to accept
# Want to replace all spaces with a '_' and delete any foreign characters such as: (, ), < and replace them with "."
# Only valid characters that are accepted: a-zA-Z0-9:_
# Using a dictionary to hold the key and value pairs
def check_stat(stat):
	invalid_characters = {" ":"_", "<":"lessthan", ">":"greaterthan", "(":"", ")":"",\
		"!":"", ".":"_", "-":"_"}
	
	for i, j in invalid_characters.iteritems():
		stat = stat.replace(i, j)
	return stat

# Feed in array in to do judgement what each of the stat names are
def check_name(c, conn, stats_epochtime, stat, value):
	ns_stat_successful = "successful"
	inc_stat_query = "QUERY"
	if ns_stat_successful in stat:
		c.execute('''INSERT INTO ns_stats VALUES(
						?,?)''', (stats_epochtime, value))
		conn.commit()
		c.execute('''SELECT * FROM ns_stats''')
		return
	elif inc_stat_query in stat:
		c.execute('''INSERT INTO incoming_requests VALUES(
						?,?)''', (stats_epochtime, value))
		conn.commit()
		c.execute('''SELECT * FROM incoming_requests''')
		return

def calculate_qps(c):
	# Get latest incoming requests
	c.execute('''SELECT inc_queries FROM incoming_requests
					ORDER BY inc_queries DESC
					LIMIT 1''')
	curr_inc_queries = c.fetchone()
	current_inc_queries = curr_inc_queries[0]
	
	
	# Get previous incoming requests
	c.execute('''SELECT inc_queries FROM incoming_requests
					ORDER BY inc_queries DESC
					limit 1,1''')
	prev_inc_queries = c.fetchone()
	previous_inc_queries = prev_inc_queries[0]
	
	qps_inc_queries = (float(current_inc_queries) - float(previous_inc_queries)) / float(QPS_SLEEP)
	
	# Get latest name server stats
	c.execute('''SELECT successful FROM ns_stats
					ORDER BY successful DESC
					LIMIT 1''')
	curr_successful_queries = c.fetchone()
	current_successful_queries = curr_successful_queries[0]
	
	
	# Get previous incoming requests
	c.execute('''SELECT successful FROM ns_stats
					ORDER BY successful DESC
					limit 1,1''')
	prev_successful_queries = c.fetchone()
	previous_successful_queries = prev_successful_queries[0]
	
	qps_successful_queries = (float(current_successful_queries) - float(previous_successful_queries)) / float(QPS_SLEEP)
	
	
	print "QPS Time Period: %s" %(QPS_SLEEP)
	print "Incoming requests QPS: %s" %(qps_inc_queries)
	print "Queries successful QPS: %s" %(qps_successful_queries)
	
	
	
# Runs rndc
def run_rndc():
	command = "%s stats" %(RNDC)
	subprocess.call([command], shell=True)
	
# Get QPS with a time interval of 10 seconds
def get_current_qps():
	# Run rndc stats
	run_rndc()

	# Copy named.stats to a separate location
	script_dir = copy_named_stats()
	
	# Create database and table. Return cursor as 'c'
	c, conn = create_db()
	
	# Output formatted stats to named.stats.formatted and epoch timestamp of the statistics dump
	formatted_stats, stats_epochtime = output_formatted_stats(script_dir)
	
	# Insert stats into SQL tables
	formatted_iteration(c, conn, stats_epochtime, formatted_stats)
	
	sleep = float(QPS_SLEEP)
	time.sleep(sleep)
	
	# 2nd run
	run_rndc()
	
	# Copy named.stats to a separate location
	script_dir = copy_named_stats()
	
	# Output formatted stats to named.stats.formatted and epoch timestamp of the statistics dump
	formatted_stats, stats_epochtime = output_formatted_stats(script_dir)
	
	# Insert stats into SQL tables
	formatted_iteration(c, conn, stats_epochtime, formatted_stats)
	
	calculate_qps(c)
	
	
	
	
def main():
	get_current_qps()
	
	
	
	
	# Run RNDC, do formatted stats again
	
	# Gather last 2 rows in DB
	
	# Do calculation and output
	
	
	
main()