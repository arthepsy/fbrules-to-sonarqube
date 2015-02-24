#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os, errno, re
import argparse
from cStringIO import StringIO
from lxml import etree

from fb import FindBugsPlugin

output_dir = 'build'

category_names = {"BAD_PRACTICE":"Bad practice",
                  "CORRECTNESS":"Correctness",
                  "MT_CORRECTNESS": "Multithreaded correctness",
                  "I18N": "Internationalization",
                  "EXPERIMENTAL": "Experimental",
                  "MALICIOUS_CODE": "Malicious code vulnerability",
                  "PERFORMANCE": "Performance",
                  "SECURITY": "Security",
                  "STYLE": "Style"}
valid_priorities = {"BLOCKER":1, "CRITICAL":1, "MAJOR":1, "MINOR":1, "INFO":1}

rule_priorities = {}
rule_tags = {}

deprecated_rules = {}
disabled_rules = {}
experimental_rules = {}
rule_order = {}


def parse_args():
	parser = argparse.ArgumentParser(
		description='Convert FindBugs rules to SonarQube rules.', 
		usage='%(prog)s [--html] <data-file> <fbrules-dir>', 
		formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=30)
	)
	parser.add_argument('data_file', metavar='data-file', help='rules data file')
	parser.add_argument('fbrules_dir', metavar='fbrules-dir', help='directory which contains findbugs.xml and messages.xml')
	parser.add_argument('--html', help='export HTML files and relevant properties file', action='store_true')
	parser.add_argument('--tidy', help='tidy HTML files', action='store_true')
	parser.add_argument('-e', '--exclude', metavar='KEY', help='rule key to completely exclude', action='append')
	parser.add_argument('-c', '--comment', metavar='KEY', help='rule key to comment out', action='append')
	return parser.parse_args()

def getpath(path_file):
	if (path_file[0] == "/"):
		return path_file
	else:
		cdir = os.path.dirname(os.path.realpath(__file__))
		return os.path.join(cdir, path_file)

def getint(s):
	try:
		return int(s)
	except ValueError:
		return 0

def init(args):
	sq_rule_file = args.data_file
	path = args.fbrules_dir
	fb_plugin = FindBugsPlugin.parse(path)
	
	if not create_output_dir():
		sys.exit('error: could not create directory for output')
	
	prefix = fb_plugin.head.short_id
	if prefix == 'core':
		prefix = 'findbugs'
	
	if args.html:
		if not create_html_dir(prefix):
			sys.exit('error: could not create directory for html files')
	
	if os.path.exists(sq_rule_file):
		for line in open(sq_rule_file):
			if line.startswith('#'): continue
			props = line.split(':')
			
			if (len(props) < 5): continue
			rule_key = props[0].strip()
			if len(rule_key) == 0: continue
			
			sq_rule_nr = getint(props[1])
			sq_prop_nr = getint(props[2])
			sq_prof_nr = getint(props[3])
			rule_order[rule_key] = [sq_rule_nr, sq_prop_nr, sq_prof_nr]
			
			priority = props[4].strip()
			if (len(priority) > 0):
				rule_priorities[rule_key] = priority
			if (len(props) < 6): continue
			states = props[5].strip()
			for state in states.split(','):
				if not state.strip(): continue
				if state == 'DEPRECATED':
					reason = props[6].strip() if len(props) > 6 else ''
					if len(reason) > 0:
						reason = reason.replace(',NotInSonarProfile', '').replace('NotInSonarProfile', '')
					deprecated_rules[rule_key] = reason
				elif state == 'DISABLED':
					disabled_rules[rule_key] = True
				elif state == 'EXPERIMENTAL':
					experimental_rules[rule_key] = True
				else:
					sys.exit('error: "%s" is invalid rule state.' % state)
			if (len(props) < 8): continue
			tags = props[7].strip()
			if len(tags) > 0:
				rule_tags[rule_key] = tags
	
	return [fb_plugin, prefix]

def create_output_dir():
	try:
		os.makedirs(output_dir)
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			return False
	return True

def create_html_dir(prefix):
	try:
		os.makedirs(os.path.join(output_dir, 'html', prefix))
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			return False
	return True

def write_file_data(filename, contents, append = False):
	fh = None
	try:
		fh = open(filename, 'a' if append else 'w')
		if contents: fh.write(contents)
	except IOError:
		return False
	finally:
		if fh: fh.close()
	return True

def get_prefix(root, defined_prefix):
	prefix = defined_prefix
	if not prefix:
		pluginid = root.get('pluginid')
		dot = pluginid.rindex('.')
		if dot > 0:
			prefix = pluginid[dot+1:]
		else:
			prefix = pluginid
	if prefix == 'core':
		prefix = 'findbugs'
	return prefix

category_override = {"NOISE": "Noise"}
category_fallback = {
	"CORRECTNESS": "Correctness",
	# "NOISE": "Bogus random noise",
	"SECURITY": "Security",
	"BAD_PRACTICE": "Bad practice",
	"STYLE": "Dodgy code",
	"PERFORMANCE": "Performance",
	"MALICIOUS_CODE": "Malicious code vulnerability",
	"MT_CORRECTNESS": "Multithreaded correctness",
	"I18N": "Internationalization",
	"EXPERIMENTAL": "Experimental"
}

def get_category_name(fb_plugin, fb_pattern):
	category = fb_pattern.category_name.strip().upper()
	if len(category) == 0:
		category = 'MISCELLANEOUS'
	if category in category_override:
		category = category_override[category]
	elif category in fb_plugin.categories:
		category = fb_plugin.categories[category].description
	if category in category_fallback:
		category = category_fallback[category]
	else:
		category = category[0] + category[1:].lower().replace('_', ' ')
	return category

def get_priority(rule_key):
	if rule_key in rule_priorities:
		priority = rule_priorities[rule_key]
		if priority == '?':
			priority = 'INFO'
		if not priority in valid_priorities:
			sys.exit('error: "%s" is invalid rule priority.' % priority)
		return priority
	else:
		return "INFO"

def get_order(rule_key):
	if rule_key in rule_order:
		return rule_order[rule_key]
	else:
		return [0, 0, 0]

def get_deprecation_text(rule_key):
	text = ''
	if rule_key in deprecated_rules:
		reason = deprecated_rules[rule_key]
		if reason == 'ByFindBugsPlugin':
			text = '\n\n<p>\nThis rule is deprecated by FindBugs.\n</p>\n'
		else:
			text = '},{rule:squid:'.join(filter(None, reason.split(',')))
			text = '{rule:squid:' + text + '}'
			text = text.replace('{rule:squid:}', '').strip()
			comma = text.rfind(',')
			if comma > -1:
				text = text[:comma] + ' and ' + text[comma+1:]
			if len(text) > 0:
				text = '\n\n<p>\nThis rule is deprecated, use %s instead.\n</p>\n' % text
	return text

def fix_html_descr(html, use_tidy):
	if use_tidy:
		from tidylib import tidy_fragment
		fragment, errors = tidy_fragment(html)
		#print "YEAH!" 
		return fragment
	print "--------------"
	#html = re.sub(r'    ','\t', html) # tabify
	html = re.sub(r'^[ ]+<p>', '<p>', html)
	lines = html.split('\n')
	tabs = -1
	for line in lines:
		m = re.search('[^\t]', line)
		if m and (tabs == -1 or m.start() < tabs):
			tabs = m.start()
	if tabs > 0:
		 html = re.sub(r'\t' * tabs, '', html)
	#html = re.sub(r'<p>([^\n]*)\n[\t ]*</p>', '<p>###\\1</p>', html)
	return html

def get_description(rule_key, details, use_tidy):
	descr_xml = details.lstrip('\r\n').rstrip('\r\n')
	descr_xml = re.sub(r'[\t ]+\n', '\n', descr_xml)
	descr_xml = descr_xml.lstrip('\r\n').rstrip()
	#use_tidy = False
	if len(descr_xml.strip()) == 0:
		descr_xml = rule_key
	descr_html = fix_html_descr(descr_xml, use_tidy)
	if rule_key in deprecated_rules:
		reason = get_deprecation_text(rule_key)
		descr_xml = descr_xml + reason
		descr_html = descr_html + reason
	
	return [descr_xml, descr_html]

def get_writer(ordered, nr):
	if not nr in ordered:
		ordered[nr] = StringIO()
		if ordered['_max'] < nr:
			ordered['_max'] = nr
	return ordered[nr]

def gen_output(output, ordered):
	for i in range(1, ordered['_max'] + 1):
		if i in ordered:
			output.write(ordered[i].getvalue())
	output.write(ordered[0].getvalue())

def parse_keys(value):
	parsed_keys = {}
	if value is not None:
		for rawkey in value:
			keys = rawkey.split(',')
			for key in keys:
				parsed_keys[key] = True
	return parsed_keys

def parse_rules(args, fb_plugin, prefix):
	
	exclude_keys = parse_keys(args.exclude)
	comment_keys = parse_keys(args.comment)
	
	findbugs_core = (prefix == 'findbugs')
	# if findbugs_core: category_names['STYLE'] = 'Dodgy'
	
	filename = 'findbugs.properties' if findbugs_core else 'findbugs-%s.properties' % prefix 
	properties_file = os.path.join(output_dir, filename)
	profile_file = os.path.join(output_dir, 'profile-%s.xml' % prefix)
	
	orules = {0:StringIO(), '_max':0}
	oprops = {0:StringIO(), '_max':0}
	oprofs = {0:StringIO(), '_max':0}
	
	for fb_pattern in sorted(fb_plugin.patterns.values(), key=lambda i:i.message_index):
		fb_key = fb_pattern.name
		if fb_key in exclude_keys: continue
		fb_details =  fb_pattern.details
		fb_shortdescr =  fb_pattern.short_desc
		
		sq_key = fb_key
		[sq_rule_nr, sq_prop_nr, sq_prof_nr] = get_order(sq_key)
		rule = get_writer(orules, sq_rule_nr)
		prop = get_writer(oprops, sq_prop_nr)
		prof = get_writer(oprofs, sq_prof_nr)
		
		sq_priority = get_priority(sq_key)
		sq_cat = get_category_name(fb_plugin, fb_pattern)
		
		sq_name = sq_cat + " - " + fb_shortdescr.strip()
		sq_config_key = sq_key
		[sq_descr_xml, sq_descr_html] = get_description(sq_key, fb_details, args.tidy)
		
		prop.write('rule.findbugs.%s.name=%s\n' % (sq_key, sq_name))
		if args.html:
			filename = os.path.join(output_dir, 'html', prefix, ('%s.html' % sq_key))
			if not write_file_data(filename, sq_descr_html):
				sys.exit('error: could not write "%s"' % filename) 
		
		if not sq_key in disabled_rules:
			prof.write('  <Match>\n')
			prof.write('    <Bug pattern="%s"/>\n' % sq_key)
			prof.write('  </Match>\n')
		
		if findbugs_core:
			rule.write('  <rule key="%s">\n' % sq_key)
			rule.write('    <priority>%s</priority>\n' % sq_priority)
		else:
			rule.write('  <rule key="%s" priority="%s">\n' % (sq_key, sq_priority))
		rule.write('    <name><![CDATA[%s]]></name>\n' % sq_name)
		rule.write('    <configKey><![CDATA[%s]]></configKey>\n' % sq_config_key)
		if sq_key in rule_tags:
			for rule_tag in rule_tags[sq_key].split(','):
				rule.write('    <tag>%s</tag>\n' % rule_tag)
		if sq_key in deprecated_rules:
			rule.write('    <status>DEPRECATED</status>\n')
		if not findbugs_core:
			rule.write('    <description><![CDATA[\n\n%s\n\n\t\t]]></description>\n' % sq_descr_xml)
		rule.write('  </rule>\n\n')
	
	props = StringIO();
	gen_output(props, oprops)
	if not write_file_data(properties_file, props.getvalue()):
		sys.exit('error: could not write "%s"' % properties_file) 
	
	profs = StringIO();
	profs.write('<?xml version="1.0" encoding="UTF-8"?>\n')
	profs.write('<!-- Generated by fb2sq -->\n')
	profs.write('<FindBugsFilter>\n')
	gen_output(profs, oprofs)
	profs.write('</FindBugsFilter>\n')
	if not write_file_data(profile_file, profs.getvalue()):
		sys.exit('error: could not write "%s"' % profile_file) 
	
	rules = StringIO();
	rules.write('<rules>\n')
	rules.write('\n' if findbugs_core else '  <!-- %s -->\n' % prefix)
	gen_output(rules, orules)
	rules.write('</rules>')
	filename = 'rules.xml' if findbugs_core else 'rules-%s.xml' % prefix 
	filename = os.path.join(output_dir, filename)
	if not write_file_data(filename, rules.getvalue()):
		sys.exit('error: could not write "%s"' % filename) 

def main():
	args = parse_args()
	parse_rules(args, *init(args))
	sys.exit(0)

if __name__ == '__main__':
	output_dir = getpath(output_dir)
	main()
