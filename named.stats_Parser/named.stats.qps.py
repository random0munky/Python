#!/usr/bin/python

# This script is used to gather the previous named.stats and compute the QPS.
# Return QPS as prometheus statistics

import re
import inspect
import textwrap
import os
import sys


SERVER = sys.argv[1]
NAMED_STATS_FILE = "/appl/node_exporter/stats/original/named.stats_%s" %(SERVER)
NAMED_STATS_FORMATTED_FILE = "/appl/node_exporter/stats/formatted/named.stats_%s_previous" %(SERVER)
NAMED_STATS_PROM_DIR = "/appl/node_exporter/stats/prom"

# This function is to read the named.stats to output formatted named.stats file
# This function is different in the sense of getting the previous statistics.
# Outputs file: ../original/named.stats_{short_hostname}_previous
def output_formatted_file(orig_file, formatted_file):
	orig_stats = open(orig_file, "r")
	orig_contents = orig_stats.readlines()
	# Gets the last line of the file and strips any carriage returns/new lines
	orig_lastline = orig_contents[-1].strip()
	# Get the epoch time of the stats dump
	orig_epochtime = re.search('\(([^)]+)', orig_lastline).group(1).strip()
	# Now that we have the epochtime, we need to get the line numbers where the epoch time exists
	# epoch_line array contains the start and end line numbers
	epoch_line = []
	prev_epoch_line = []
	new_stats = open(formatted_file, "w")
	for num, line in enumerate(orig_contents, 1):
		if orig_epochtime in line:
			#print "Found epochtime at this line number: %s" %(num)
			epoch_line.append(num)
	# Now that I have the epoch time of the latest stats dump (start and finish), lets find the previous stats dump epoch time.
	prev_epochtime = orig_contents[epoch_line[0] - 2]
	prev_epochtime = re.search('\(([^)]+)', prev_epochtime).group(1).strip()
	for num, line in enumerate(orig_contents, 1):
		if prev_epochtime in line:
			prev_epoch_line.append(num)
	# This for loop takes the two epoch array values (had to -1 for the starting value because it was getting left out)
	# Which then writes the line contents from the range between the two values to a 2nd file.
	for line in range((prev_epoch_line[0] - 1), prev_epoch_line[1]):
			new_stats.write(orig_contents[line])
	
	return formatted_file

# This function is to take the formatted named.stats file, parse through the file given line number ranges
# Save each of the section's values inside the named.stats file, into arrays. Return arrays.
# UPDATE 9/27/18 - Outputting a tuple array which contains: (stat_value, stat name)
# This way, the statistics are "flexible" in the sense of logging all types of traffic. No traffic shall be left out.
# In addition, record the type of record as well.
def formatted_iteration(formatted_file):
	new_stats = open(formatted_file, "r")
	new_content = new_stats.readlines()
	section_line = []
	# Lets look for lines that start with a "++".
	# Get the line numbers for each of the sections; they start with a "++"
	for num, line in enumerate(new_content, 1):
		if line.startswith("++ "):
			section_line.append(num)
			
	# Index for which array I'm looping through for adding values to.
	array_index = 0
	# Type of metric (counter, gauge, or histogram)
	metric_type = "gauge"
	# For loops to go through each section of the named.stats file
	#Incoming Requests: QUERY, etc.
	prev_incoming_requests = []
	for line in range(section_line[0], (section_line[1] - 1)):
		inc_request = new_content[line].strip()
		inc_value = inc_request.split(' ', 1)[0]
		inc_stat = inc_request.split(' ', 1)[1]
		inc_stat = check_stat(inc_stat)
		tuple = inc_value, inc_stat, metric_type
		prev_incoming_requests.append(tuple)
	#print "Incoming Requests: %s" %(incoming_requests)
	
	# Incoming Queries: A, PTR, AAAA, NAPTR, ANY, etc.
	prev_incoming_queries = []
	for line in range(section_line[1], (section_line[2] - 1)):
		inc_query = new_content[line].strip()
		inc_value = inc_query.split(' ', 1)[0]
		query_stat = inc_query.split(' ',1)[1]
		query_stat = check_stat(query_stat)
		tuple = inc_value, query_stat, metric_type
		prev_incoming_queries.append(tuple)
	#print "Incoming Queries: %s" %(incoming_queries)
	
	# Outgoing Queries: A, PTR, AAAA, NAPTR, ANY, etc
	prev_outgoing_queries = []
	for line in range(section_line[2] + 1, (section_line[3] - 2)):
		out_query = new_content[line].strip()
		out_value = out_query.split(' ', 1)[0]
		query_stat = out_query.split(' ',1)[1]
		query_stat = check_stat(query_stat)
		tuple = out_value, query_stat, metric_type
		prev_outgoing_queries.append(tuple)
	#print "Outgoing Queries: %s" %(outgoing_queries)
	
	# Name Server Statistics: IPv4 requests received, requests with EDNS(0) received, TCP requests received, responses sent, truncated responses sent, responses with EDNS(0) sent, queries resulted in successful answer, queries resulted in authoritative answer, queries resulted in non authoritative answer, queries resulted in nxrrset, queries resulted in SERVFAIL, queries resulted in NXDOMAIN, queries caused recursion, queries dropped, UDP queries received, TCP queries received
	prev_ns_stats = []
	for line in range(section_line[3], (section_line[4] - 1)):
		ns_stat = new_content[line].strip()
		ns_value = ns_stat.split(' ', 1)[0]
		ns_stat = ns_stat.split(' ',1)[1]
		ns_stat = check_stat(ns_stat)
		tuple = ns_value, ns_stat, metric_type
		prev_ns_stats.append(tuple)
	#print "Name Server Stats: %s" %(ns_stats)
	
	# Resolver Statistics: IPv4 queries sent, IPv4 responses received, NXDOMAIN received, SERVFAIL received, truncated responses received, lame delegations received, query retries, query timeouts, IPv4 NS address fetches, IPv6 NS address fetches, IPv4 NS address fetch failed, IPv6 NS address fetch failed, queries with RTT < 10ms, queries with RTT 10-100ms, queries with RTT 100-500ms, queries with RTT 500-800ms, queries with RTT 800-1600ms, bucket size, SIT sent client cookie only
	# Had to skip an array value to be in the Resolver Statistics section of the file.
	prev_resolver_stats = []
	for line in range(section_line[5] + 2, (section_line[6] - 3)):
		resolver_stat = new_content[line].strip()
		resolver_value = resolver_stat.split(' ', 1)[0]
		resolver_stat = resolver_stat.split(' ',1)[1]
		resolver_stat = check_stat(resolver_stat)
		tuple = resolver_value, resolver_stat, metric_type
		prev_resolver_stats.append(tuple)
	#print "Resolver Stats: %s" %(resolver_stats)
	
	# Return each of the arrays for another function to do the formatting
	return prev_incoming_requests, prev_incoming_queries, prev_outgoing_queries, prev_ns_stats, prev_resolver_stats

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

# This function is used to iterate a file_index which I refer to with the 'output_prometheus_metrics' function
def make_prometheus_metrics(incoming_requests, incoming_queries, outgoing_queries, ns_stats, resolver_stats):
	# This is the counter I will use to determine which named.stats array I am going through
	file_index = 0
	
	# Incoming Requests
	file_index=0
	metric_note = "inc_req"
	output_prometheus_metrics(incoming_requests, file_index, metric_note)

	# Incoming Queries
	file_index+=1
	metric_note = "inc_query"
	output_prometheus_metrics(incoming_queries, file_index, metric_note)
	
	# Outgoing Queries
	file_index+=1
	metric_note = "out_query"
	output_prometheus_metrics(outgoing_queries, file_index, metric_note)
	
	# Name Server Statistics
	file_index+=1
	metric_note = "ns_stat"
	output_prometheus_metrics(ns_stats, file_index, metric_note)	
	
	# Resolver Stats
	file_index+=1
	metric_note = "resolver_stat"
	output_prometheus_metrics(resolver_stats, file_index, metric_note)
	
def output_prometheus_metrics(named_stats_array, file_index, metric_note):
	# To set variables for each of the metric files
	inc_req_prom = "%s/%s_named_incoming_requests.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	inc_query_prom = "%s/%s_named_incoming_queries.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	out_query_prom = "%s/%s_named_outgoing_queries.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	ns_stat_prom = "%s/%s_named_ns_stats.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	resolver_prom = "%s/%s_named_resolver.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	
	# Have all the files inside an array which we'll iterate through with the file_index variables
	file_array = [ inc_req_prom, inc_query_prom, out_query_prom, ns_stat_prom, resolver_prom ]
	
	# Clear out only the file that we are working with
	# Giving the "a" parameter will append to the file
	open(file_array[file_index], "w").close()
	prom_file = open(file_array[file_index], "a")
	
	# metric_array contains [ {metric_name} {metric_description} {metric_type} ]
	# named_stats_array contains [ {metric_value} {metric_name} {file_index} ]
	# For the metric_name, want to add the server hostname that the metrics belong to
	for element in named_stats_array:
		metric_name = "%s_%s_%s" %(SERVER, element[1], metric_note)
		metric_value = element[0]
		metric_type = element[2]
		metric_text = textwrap.dedent("""\
			# HELP %s %s
			# TYPE %s %s
			%s %s
			
			""") %(metric_name, metric_name, metric_name, metric_type, metric_name, metric_value)
		# Write a separate file for each section of named.stats since there's a line/size limit that node_exporter can take in
		prom_file.write(metric_text)
		
def import_arrays():
	incoming_requests = sys.argv[2]
	incoming_queries = sys.argv[3]
	outgoing_queries = sys.argv[4]
	ns_stats = sys.argv[5]
	resolver_stats sys.argv[6]
		
def main():
	output_formatted_file(NAMED_STATS_FILE, NAMED_STATS_FORMATTED_FILE)
	#incoming_requests, incoming_queries, outgoing_queries, ns_stats, resolver_stats = \
	#formatted_iteration(NAMED_STATS_FORMATTED_FILE)
	#make_prometheus_metrics(incoming_requests, incoming_queries, outgoing_queries, ns_stats, resolver_stats)
	
main()
