#!/usr/bin/python

# First step is to read-in the named.stats file, find the last line (epoch time), find the (epoch time) of the beginning of the stats dump, cut out the rest and leave only the most recent stats dump. Output to formatted/named.stats file.
# This accomplishes to get the most recent stats dump which will be easier to work with later.

# Second step is to read-in the modified named.stats file, be able to iterate through each of the sections of the stats dump:
# Incoming Requests, Incoming Queries, Outgoing Queries, Name Server Statistics, Zone Mainentenance Statistics

# Third step is to format each of the metrics into prometheus's template:
# # HELP ntpd_rootdisp NTPd metric for rootdisp
# TYPE ntpd_rootdisp gauge
# ntpd_rootdisp 0.270000

# UPDATE: 9/27/18
# Fourth, I find that it's easier to use the stat name instead of hard coding a name. This way, the stats can be flexible
# This update is in response with finding that rndc stats dumps a stats file which do not have all of the possible stats rndc stats is able to output
# Depending on what traffic BIND handles, there could be traffic that I don't account for.
# SERVER variable tells which server script is parsing
# NAMED_STATS_GENERATION variable indicates how often named stats dump is executed on target servers in SECONDS.

import re
import inspect
import textwrap
import os
import sys


#SERVER = sys.argv[1]
SERVER = "wtc2b1fdns01v"
NAMED_STATS_FILE = "/appl/node_exporter/stats/original/named.stats_%s" %(SERVER)
NAMED_STATS_FORMATTED_FILE_CURRENT = "/appl/node_exporter/stats/formatted/named.stats_%s" %(SERVER)
NAMED_STATS_FORMATTED_FILE_PREVIOUS = "/appl/node_exporter/stats/formatted/previous.named.stats_%s" %(SERVER)
NAMED_STATS_PROM_DIR = "/appl/node_exporter/stats/prom"
NAMED_STATS_GENERATION = "300"

# This function is to read the named.stats to output formatted named.stats file
# In addition reads the named.stats second to last stats dump entry and output formatted previous.named.stats file
def output_formatted_file(orig_file, formatted_current, formatted_previous):
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
	new_stats = open(formatted_current, "w")
	prev_stats = open(formatted_previous, "w")
	for num, line in enumerate(orig_contents, 1):
		if orig_epochtime in line:
			#print "Found epochtime at this line number: %s" %(num)
			epoch_line.append(num)
			
	# Now that I have the epoch time of the latest stats dump (start and finish), lets find the previous stats dump epoch time.
	prev_epochtime_line = orig_contents[epoch_line[0] - 2]
	prev_epochtime = re.search('\(([^)]+)', prev_epochtime_line).group(1).strip()
	for num, line in enumerate(orig_contents, 1):
		if prev_epochtime in line:
			prev_epoch_line.append(num)
	# This for loop takes the two epoch array values (had to -1 for the starting value because it was getting left out)
	# Which then writes the line contents from the range between the two values to a 2nd file.
	for line in range((epoch_line[0] - 1), epoch_line[1]):
		new_stats.write(orig_contents[line])
	
	for line in range((prev_epoch_line[0] - 1), prev_epoch_line[1]):
		prev_stats.write(orig_contents[line])
	return formatted_current, formatted_previous

# This function is to take the formatted named.stats file, parse through the file given line number ranges
# Save each of the section's values inside the named.stats file, into arrays. Return arrays.
# UPDATE 9/27/18 - Outputting a tuple array which contains: (stat_value, stat name)
# This way, the statistics are "flexible" in the sense of logging all types of traffic. No traffic shall be left out.
# In addition, record the type of record as well.
# Example output: Incoming Queries: [('145864', 'A', 'gauge'), ('3', 'SOA', 'gauge'), ('1718', 'PTR', 'gauge'), ('271', 'HINFO', 'gauge'), ('136965', 'AAAA', 'gauge'), ('1', 'SRV', 'gauge'), ('1', 'ANY', 'gauge')]

def formatted_iteration(formatted_file):
	new_stats = open(formatted_file, "r")
	new_content = new_stats.readlines()
	
	# Creating line number arrays for each section of the named.stats file
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
	# Type of metric (counter, gauge, or histogram)
	metric_type = "gauge"
	# For loops to go through each section of the named.stats file
	# The if statement checks if the line starts with a digit. If it does not, pass to next line.
	#Incoming Requests: QUERY, etc.
	incoming_requests = []
	for line in range(inc_req_line[0], (inc_query_line[0] - 1)):
		inc_request = new_content[line].strip()
		if inc_request[0].isdigit():
			inc_value = inc_request.split(' ', 1)[0]
			inc_stat = inc_request.split(' ', 1)[1]
			inc_stat = check_stat(inc_stat)
			tuple = inc_value, inc_stat, metric_type
			incoming_requests.append(tuple)
		else:
			pass
	#print "Incoming Requests: %s" %(incoming_requests)
	
	# Incoming Queries: A, PTR, AAAA, NAPTR, ANY, etc.
	incoming_queries = []
	for line in range(inc_query_line[0], (out_rcodes_line[0] - 1)):
		inc_query = new_content[line].strip()
		if inc_query[0].isdigit():
			inc_value = inc_query.split(' ', 1)[0]
			query_stat = inc_query.split(' ',1)[1]
			query_stat = check_stat(query_stat)
			tuple = inc_value, query_stat, metric_type
			incoming_queries.append(tuple)
		else:
			pass
	#print "Incoming Queries: %s" %(incoming_queries)
	
	# Outgoing Rcodes: NOERROR, SERVFAIL, NXDOMAIN
	outgoing_rcodes = []
	for line in range(out_rcodes_line[0], (out_query_line[0] -1)):
		rcode_query = new_content[line].strip()
		if rcode_query[0].isdigit():
			rcode_query_value = rcode_query.split(' ', 1)[0]
			query_stat = rcode_query.split(' ',1)[1]
			rcode_query_stat = check_stat(query_stat)
			tuple = rcode_query_value, rcode_query_stat, metric_type
			outgoing_rcodes.append(tuple)
		else:
			pass
	#print "Outgoing Rcodes: %s" %(outgoing_rcodes)
	
	# Outgoing Queries: A, PTR, AAAA, NAPTR, ANY, etc
	outgoing_queries = []
	for line in range(out_query_line[0], (ns_query_line[0] - 1)):
		out_query = new_content[line].strip()
		if out_query[0].isdigit():
			out_value = out_query.split(' ', 1)[0]
			query_stat = out_query.split(' ',1)[1]
			query_stat = check_stat(query_stat)
			tuple = out_value, query_stat, metric_type
			outgoing_queries.append(tuple)
		else:
			pass
	#print "Outgoing Queries: %s" %(outgoing_queries)
	
	# Name Server Statistics: IPv4 requests received, requests with EDNS(0) received, TCP requests received, responses sent, truncated responses sent, responses with EDNS(0) sent, queries resulted in successful answer, queries resulted in authoritative answer, queries resulted in non authoritative answer, queries resulted in nxrrset, queries resulted in SERVFAIL, queries resulted in NXDOMAIN, queries caused recursion, queries dropped, UDP queries received, TCP queries received
	ns_stats = []
	for line in range(ns_query_line[0], (resolver_line[0] - 1)):
		ns_stat = new_content[line].strip()
		if ns_stat[0].isdigit():
			ns_value = ns_stat.split(' ', 1)[0]
			ns_stat = ns_stat.split(' ',1)[1]
			ns_stat = check_stat(ns_stat)
			tuple = ns_value, ns_stat, metric_type
			ns_stats.append(tuple)
		else:
			pass
	#print "Name Server Stats: %s" %(ns_stats)
	#for tuple in ns_stats:
	#	print tuple
	
	#Resolver Statistics: IPv4 queries sent, IPv4 responses received, NXDOMAIN received, SERVFAIL received, truncated responses received, lame delegations received, query retries, query timeouts, IPv4 NS address fetches, IPv6 NS address fetches, IPv4 NS address fetch failed, IPv6 NS address fetch failed, queries with RTT < 10ms, queries with RTT 10-100ms, queries with RTT 100-500ms, queries with RTT 500-800ms, queries with RTT 800-1600ms, bucket size, SIT sent client cookie only
	# Had to skip an array value to be in the Resolver Statistics section of the file.
	resolver_stats = []
	for line in range(resolver_line[0], (cache_line[0] - 1)):
		resolver_stat = new_content[line].strip()
		if resolver_stat[0].isdigit():
			resolver_value = resolver_stat.split(' ', 1)[0]
			resolver_stat = resolver_stat.split(' ',1)[1]
			resolver_stat = check_stat(resolver_stat)
			tuple = resolver_value, resolver_stat, metric_type
			resolver_stats.append(tuple)
		else:
			pass
	#print "Resolver Stats: %s" %(resolver_stats)
	#for tuple in resolver_stats:
	#	print tuple
	
	# Return each of the arrays for another function to do the formatting
	return incoming_requests, incoming_queries, outgoing_queries, ns_stats, resolver_stats

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
# 1.) Check Lists to make sure there are same number of list elements comparing current and previous
# 2.) Generate QPS array for each of the lists
# 3.) Output prometheus metric format
def make_prometheus_metrics(incoming_requests, incoming_queries, outgoing_queries, ns_stats, resolver_stats, prev_incoming_requests, prev_incoming_queries, prev_outgoing_queries, prev_ns_stats, prev_resolver_stats):
	
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
	
	# Caclulate QPS metrics
	# Incoming Requests QPS
	file_index+=1
	metric_note = "qps_inc_req"
	checked_prev_incoming_requests = check_arrays(incoming_requests, prev_incoming_requests)
	qps_incoming_requests = calculate_qps(incoming_requests, checked_prev_incoming_requests)
	output_prometheus_metrics(qps_incoming_requests, file_index, metric_note)
	
	# Incoming Queries QPS
	file_index +=1
	metric_note = "qps_inc_query"
	checked_prev_incoming_queries = check_arrays(incoming_queries, prev_incoming_queries)
	qps_incoming_queries = calculate_qps(incoming_queries, checked_prev_incoming_queries)
	output_prometheus_metrics(qps_incoming_queries, file_index, metric_note)
	
	# Outgoing Queries QPS
	file_index +=1
	metric_note = "qps_out_query"
	checked_prev_outgoing_queries = check_arrays(outgoing_queries, prev_outgoing_queries)
	qps_outgoing_queries = calculate_qps(outgoing_queries, checked_prev_outgoing_queries)
	output_prometheus_metrics(qps_outgoing_queries, file_index, metric_note)
	
	# Name Server Statistics QPS
	file_index +=1
	metric_note = "qps_ns_stat"
	checked_prev_ns_stats = check_arrays(ns_stats, prev_ns_stats)
	qps_ns_stats = calculate_qps(ns_stats, checked_prev_ns_stats)
	output_prometheus_metrics(qps_ns_stats, file_index, metric_note)
	
	# Resolver Stats QPS
	file_index +=1
	metric_note = "qps_resolver_stat"
	checked_prev_resolver_stats = check_arrays(resolver_stats, prev_resolver_stats)
	qps_resolver_stats = calculate_qps(resolver_stats, checked_prev_resolver_stats)
	output_prometheus_metrics(qps_resolver_stats, file_index, metric_note)
	
	# Caclulate Delta metrics
	# Incoming Requests Delta
	file_index+=1
	metric_note = "delta_inc_req"
	checked_prev_incoming_requests = check_arrays(incoming_requests, prev_incoming_requests)
	delta_incoming_requests = calculate_delta(incoming_requests, checked_prev_incoming_requests)
	output_prometheus_metrics(delta_incoming_requests, file_index, metric_note)
	
	# Incoming Queries QPS
	file_index +=1
	metric_note = "delta_inc_query"
	checked_prev_incoming_queries = check_arrays(incoming_queries, prev_incoming_queries)
	delta_incoming_queries = calculate_delta(incoming_queries, checked_prev_incoming_queries)
	output_prometheus_metrics(delta_incoming_queries, file_index, metric_note)
	
	# Outgoing Queries QPS
	file_index +=1
	metric_note = "delta_out_query"
	checked_prev_outgoing_queries = check_arrays(outgoing_queries, prev_outgoing_queries)
	delta_outgoing_queries = calculate_delta(outgoing_queries, checked_prev_outgoing_queries)
	output_prometheus_metrics(delta_outgoing_queries, file_index, metric_note)
	
	# Name Server Statistics delta
	file_index +=1
	metric_note = "delta_ns_stat"
	checked_prev_ns_stats = check_arrays(ns_stats, prev_ns_stats)
	delta_ns_stats = calculate_delta(ns_stats, checked_prev_ns_stats)
	output_prometheus_metrics(delta_ns_stats, file_index, metric_note)
	
	# Resolver Stats delta
	file_index +=1
	metric_note = "delta_resolver_stat"
	checked_prev_resolver_stats = check_arrays(resolver_stats, prev_resolver_stats)
	delta_resolver_stats = calculate_delta(resolver_stats, checked_prev_resolver_stats)
	output_prometheus_metrics(delta_resolver_stats, file_index, metric_note)
	
	
# This function is used to set variable to prom file file paths.
# Assign correct metrics for each file associated prom file.
# Populate the prom file with the proper metric and metric value in using the proper prom template.
# Example of prom template for metrics:
## HELP wtc2b1fdns01v_QUERY_inc_req wtc2b1fdns01v_QUERY_inc_req
## TYPE wtc2b1fdns01v_QUERY_inc_req gauge
#wtc2b1fdns01v_QUERY_inc_req 285071


## HELP wtc2b1fdns01v_A_inc_query wtc2b1fdns01v_A_inc_query
## TYPE wtc2b1fdns01v_A_inc_query gauge
#wtc2b1fdns01v_A_inc_query 145991

def output_prometheus_metrics(named_stats_array, file_index, metric_note):
	# To set variables for each of the metric files
	inc_req_prom = "%s/%s_named_incoming_requests.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	inc_query_prom = "%s/%s_named_incoming_queries.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	out_query_prom = "%s/%s_named_outgoing_queries.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	ns_stat_prom = "%s/%s_named_ns_stats.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	resolver_prom = "%s/%s_named_resolver.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	qps_inc_req_prom = "%s/%s_qps_named_incoming_requests.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	qps_inc_query_prom = "%s/%s_qps_named_incoming_queries.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	qps_out_query_prom = "%s/%s_qps_named_outgoing_queries.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	qps_ns_stat_prom = "%s/%s_qps_named_ns_stats.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	qps_resolver_prom = "%s/%s_qps_named_resolver.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	delta_inc_req_prom = "%s/%s_delta_named_incoming_requests.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	delta_inc_query_prom = "%s/%s_delta_named_incoming_queries.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	delta_out_query_prom = "%s/%s_delta_named_outgoing_queries.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	delta_ns_stat_prom = "%s/%s_delta_named_ns_stats.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	delta_resolver_prom = "%s/%s_delta_named_resolver.prom" %(NAMED_STATS_PROM_DIR, SERVER)
	
	# Have all the files inside an array which we'll iterate through with the file_index variables
	file_array = [ inc_req_prom, inc_query_prom, out_query_prom, ns_stat_prom, resolver_prom,\
	qps_inc_req_prom, qps_inc_query_prom, qps_out_query_prom, qps_ns_stat_prom, qps_resolver_prom,\
	delta_inc_req_prom, delta_inc_query_prom, delta_out_query_prom, delta_ns_stat_prom, delta_resolver_prom ]
	
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
		print metric_text

# This function is used to check if there are same number of array elements in previous and current arrays
# If there is a missing array element in previous array compared to current array:
#	1. Create missing array element with a 0 metric value
# 	2. Insert array element where it should be in previous array
def check_arrays(current_array, previous_array):
	metric_type = "gauge"
	for element in current_array:
		element_index = current_array.index(element)
		try:
			if element[1] not in previous_array[element_index]:
				missing_value = "0"
				missing_tuple = missing_value, element[1], metric_type
				previous_array.insert(element_index, missing_tuple)
		except IndexError as IE:
			missing_value = "0"
			missing_tuple = missing_value, element[1], metric_type
			previous_array.insert(element_index, missing_tuple)
	return previous_array

# This function is used to calculate the QPS when being passed the most current stats dump array and previous stats dump array
# Takes in the current array and previous array
def calculate_qps(current_array, previous_array):
	stats_generation = NAMED_STATS_GENERATION
	qps_array = []
	#print "Current Array: %s" %(current_array)
	#print "Previous Array: %s" %(previous_array)
	for element in current_array:
		index = current_array.index(element)
		current_value = element[0]
		current_type = element[2]
		previous_value = previous_array[index][0]
		#print "Current_value: %s - Previous_value: %s / stats_generation: %s" %(current_value, previous_value, stats_generation)
		qps = (float(current_value) - float(previous_value)) / float(stats_generation)
		qps_tuple = float(qps), element[1], current_type
		qps_array.append(qps_tuple)
	#print "QPS Array: %s" %(qps_array)
	return qps_array
	
# This function is used to calculate the delta of the current stats dump from the previous stats dump
def calculate_delta(current_array, previous_array):
	delta_array = []
	for element in current_array:
		index = current_array.index(element)
		current_value = element[0]
		current_type = element[2]
		previous_value = previous_array[index][0]
		delta = (float(current_value) - float(previous_value))
		delta_tuple = float(delta), element[1], current_type
		delta_array.append(delta_tuple)
	return delta_array
	
def main():
	# Output formatted files for current and previous stats dumps
	output_formatted_file(NAMED_STATS_FILE, NAMED_STATS_FORMATTED_FILE_CURRENT, NAMED_STATS_FORMATTED_FILE_PREVIOUS)
	# Output arrays for current stats dump
	incoming_requests, incoming_queries, outgoing_queries, ns_stats, resolver_stats = \
	formatted_iteration(NAMED_STATS_FORMATTED_FILE_CURRENT)
	# Output arrays for previous stats dump
	prev_incoming_requests, prev_incoming_queries, prev_outgoing_queries, prev_ns_stats, prev_resolver_stats = \
	formatted_iteration(NAMED_STATS_FORMATTED_FILE_PREVIOUS)
	# Make prometheus metrics for current stats dump
	# The actual calculating of QPS for the metrics will happen inside the 'make_prometheus_metrics' function
	make_prometheus_metrics(incoming_requests, incoming_queries, outgoing_queries, ns_stats, resolver_stats,\
		prev_incoming_requests, prev_incoming_queries, prev_outgoing_queries, prev_ns_stats, prev_resolver_stats)
	
main()
