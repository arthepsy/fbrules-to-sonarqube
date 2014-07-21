#!/usr/bin/env python
import sys, os, re
from lxml import etree

if (len(sys.argv) < 2):
	sys.exit('usage: %s <fbrules-directory> [prefix]' % sys.argv[0])

fbplugin_xml = sys.argv[1] + '/findbugs.xml'
if not os.path.exists(fbplugin_xml):
	sys.exit('error: "%s" does not exist' % fbplugin_xml)

messages_xml = sys.argv[1] + '/messages.xml'
if not os.path.exists(messages_xml):
	sys.exit('error: "%s" does not exist' % messages_xml)

tree = etree.parse(fbplugin_xml)
root = tree.getroot()

prefix = ''
if (len(sys.argv) > 2):
	prefix = sys.argv[2].strip()
if not prefix:
	pluginid = root.get('pluginid')
	dot = pluginid.rindex('.')
	if dot > 0:
		prefix = pluginid[dot+1:]
	else:
		prefix = pluginid

rule_type_to_category = {}
for e in root.iter("BugPattern"):
	rule_type_to_category[e.get('type')] = e.get('category')

tree = etree.parse(messages_xml)
root = tree.getroot()

print '<!-- %s -->' % (prefix)
print '<rules>\n'

for e in root.iter("BugPattern"):
	fb_details =  e.find("Details")
	fb_shortdescr =  e.find("ShortDescription")
	fb_key = e.get("type")
	
	sq_key = fb_key
	sq_priority = "INFO"
	sq_cat = ''
	if sq_key in rule_type_to_category:
		sq_cat = rule_type_to_category[sq_key].strip()
	if len(sq_cat) == 0:
		sq_cat = 'UNKNOWN'
	sq_cat = sq_cat[0] + sq_cat[1:].lower()
	sq_name = sq_cat + " - " + fb_shortdescr.text.strip() + ' [' + prefix + ']'
	sq_config_key = sq_key
	sq_descr = re.sub(r'\t\t\t', '', fb_details.text.lstrip().rstrip())
	sq_descr = re.sub(r'\t', '  ', sq_descr)
	
	print '  <rule key="%s" priority="%s">' % (sq_key, sq_priority)
	print '    <name><![CDATA[%s]]></name>' % (sq_name)
	print '    <configKey><![CDATA[%s]]></configKey>' % (sq_config_key)
	print '    <description>\n<![CDATA[\n%s\n]]>\n    </description>' % (sq_descr)
	print '  </rule>\n'
	
print "</rules>"
