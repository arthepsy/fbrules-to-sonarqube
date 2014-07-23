#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os, errno, re
import argparse
from cStringIO import StringIO
from lxml import etree

categories = {"BAD_PRACTICE":"Bad practice",
              "CORRECTNESS":"Correctness",
              "MT_CORRECTNESS": "Multithreaded correctness",
              "I18N": "Internationalization",
              "EXPERIMENTAL": "Experimental",
              "MALICIOUS_CODE": "Malicious code",
              "PERFORMANCE": "Performance",
              "SECURITY": "Security",
              "STYLE": "Style"}

def parse_args():
	parser = argparse.ArgumentParser(
		description='Convert FindBugs rules to SonarQube rules.', 
		usage='%(prog)s [--html] fbrules-directory [component-name]', 
		formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=30)
	)
	parser.add_argument('fbrules_dir', metavar='fbrules-directory', help='directory which contains findbugs.xml and messages.xml')
	parser.add_argument('component_name', metavar='component-name', nargs='?', help='component name (core, fb-contrib, find-sec-bugs, ...)')
	parser.add_argument('--html', help='export HTML files and relevant properties file', action='store_true')
	parser.add_argument('-e', '--exclude', metavar='KEY', help='rule key to completely exclude', action='append')
	parser.add_argument('-c', '--comment', metavar='KEY', help='rule key to comment out', action='append')
	return parser.parse_args()

def init(args):
	fbplugin_xml = args.fbrules_dir + '/findbugs.xml'
	if not os.path.exists(fbplugin_xml):
		sys.exit('error: "%s" does not exist' % fbplugin_xml)
	
	messages_xml = args.fbrules_dir + '/messages.xml'
	if not os.path.exists(messages_xml):
		sys.exit('error: "%s" does not exist' % messages_xml)
	
	if args.html:
		if not create_html_dir():
			sys.exit('error: could not create directory for html files')
	
	return [fbplugin_xml, messages_xml]

def create_html_dir():
	try:
		os.makedirs('html')
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

def get_category(name):
	if name in categories:
		return categories[name]
	else:
		return name[0] + name[1:].lower()

def parse_keys(value):
	parsed_keys = {}
	if value is not None:
		for rawkey in value:
			keys = rawkey.split(',')
			for key in keys:
				parsed_keys[key] = True
	return parsed_keys

def parse_rules(args, fbplugin_xml, messages_xml):
	
	exclude_keys = parse_keys(args.exclude)
	comment_keys = parse_keys(args.comment)
	
	tree = etree.parse(fbplugin_xml)
	root = tree.getroot()
	
	prefix = args.component_name
	if not prefix:
		pluginid = root.get('pluginid')
		dot = pluginid.rindex('.')
		if dot > 0:
			prefix = pluginid[dot+1:]
		else:
			prefix = pluginid
	if prefix == 'core':
		prefix = 'findbugs'
	
	rule_type_to_category = {}
	for e in root.iter("BugPattern"):
		rule_type_to_category[e.get('type')] = e.get('category')

	properties_file = 'findbugs-%s.properties' % prefix
	if args.html:
		if not write_file_data(properties_file, None):
			sys.exit('error: could not write "%s"' % properties_file)
	
	tree = etree.parse(messages_xml)
	root = tree.getroot()

	rules = StringIO();
	rules.write('<!-- %s -->\n' % prefix)
	rules.write('<rules>\n\n')

	for e in root.iter("BugPattern"):
		fb_details =  e.find("Details")
		fb_shortdescr =  e.find("ShortDescription")
		fb_key = e.get("type")
		
		if fb_key in exclude_keys:
			continue
		
		sq_key = fb_key
		sq_priority = "INFO"
		sq_cat = ''
		if sq_key in rule_type_to_category:
			sq_cat = rule_type_to_category[sq_key].strip()
		if len(sq_cat) == 0:
			sq_cat = 'MISCELLANEOUS'
		sq_cat = get_category(sq_cat)
		sq_name = sq_cat + " - " + fb_shortdescr.text.strip()
		sq_config_key = sq_key
		sq_descr = re.sub(r'\t\t\t', '', fb_details.text.lstrip().rstrip())
		sq_descr = re.sub(r'\t', '  ', sq_descr)
		
		if len(sq_descr.strip()) == 0:
			subxml = etree.fromstring(etree.tostring(fb_details))
			etree.cleanup_namespaces(subxml)
			sq_descr = re.sub(r'\n            ', '\n', ''.join([etree.tostring(e, pretty_print=False) for e in subxml]))
			if len(sq_descr.strip()) == 0:
				sq_descr = sq_name
		
		if args.html:
			if not write_file_data(properties_file, 'rule.findbugs.%s.name=%s\n' % (sq_key, sq_name), True):
				sys.exit('error: could not write "%s"' % properties_file)
			
			filename = 'html/%s.html' % sq_key
			if not write_file_data(filename, sq_descr + '\n'):
				sys.exit('error: could not write "%s"' % filename) 
		
		if prefix != 'findbugs':
			sq_name = sq_name  + ' [' + prefix + ']'
		
		rules.write('  <rule key="%s" priority="%s">\n' % (sq_key, sq_priority))
		rules.write('    <name><![CDATA[%s]]></name>\n' % sq_name)
		rules.write('    <configKey><![CDATA[%s]]></configKey>\n' % sq_config_key)
		rules.write('    <description>\n<![CDATA[\n%s\n]]>\n    </description>\n' % sq_descr)
		rules.write('  </rule>\n\n')
		
	rules.write('</rules>\n')
	
	filename = 'rules-%s.xml' % prefix
	if not write_file_data(filename, rules.getvalue()):
		sys.exit('error: could not write "%s"' % filename) 
	

def main():
	args = parse_args()
	parse_rules(args, *init(args))
	sys.exit(0)

if __name__ == '__main__':
	main()
