#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
   The MIT License (MIT)
   
   Copyright (C) 2015 Andris Raugulis (moo@arthepsy.eu)
   
   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction, including without limitation the rights
   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   copies of the Software, and to permit persons to whom the Software is
   furnished to do so, subject to the following conditions:
   
   The above copyright notice and this permission notice shall be included in
   all copies or substantial portions of the Software.
   
   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   THE SOFTWARE.
"""
import os, re
from lxml import etree

class SqXml():
	@staticmethod
	def get_attr_value(xnode, attr_name):
		return (xnode.get(attr_name) or '').strip()
	
	@staticmethod
	def get_node(xnode, child_name):
		return xnode.find('{*}' + child_name)
	
	@staticmethod
	def get_nodes(xnode, child_name):
		return xnode.iterfind('{*}' + child_name)
	
	@staticmethod
	def get_node_text(xnode, default_value=None, clean=False):
		if xnode is not None and xnode.text is not None:
			value = xnode.text.strip()
		else:
			value = ''
		if len(value) == 0 and default_value is not None:
			value = default_value
		return SqUtils.get_clean(value) if clean else value
	
	@staticmethod
	def get_cnode_text(xnode, child_name, default_value=None, clean=False):
		xnode = SqXml.get_node(xnode, child_name)
		return SqXml.get_node_text(xnode, default_value, clean)

class SqUtils():
	@staticmethod
	def parse_int(s):
		return int(SqUtils.parse_num(s))
	
	@staticmethod
	def parse_dec(s):
		try:
			return float(s)
		except ValueError:
			return 0
		 
	@staticmethod
	def parse_num(s): 
		try: 
			return int(s)
		except ValueError:
			return SqUtils.parse_dec(s)
	
	@staticmethod
	def get_clean(text):
		return re.sub(r'[\n\t\s]+', ' ', text).strip()
	
	@staticmethod
	def get_dir(p):
		return os.path.realpath(os.path.expanduser(p))
	
	@staticmethod
	def get_file(p, root = None):
		p = os.path.expanduser(p)
		if not os.path.isabs(p):
			if root is None:
				root = os.path.dirname(os.path.realpath(__file__))
			root = SqUtils.get_dir(root)
			p = os.path.join(root, p)
		return os.path.realpath(p)

class SonarQube(object):
	class Rules(dict):
		def __init__(self, *args, **kwargs):
			dict.__init__(self, *args, **kwargs)
			
		@staticmethod
		def find_dir(plugin_dir):
			plugin_dir = SqUtils.get_dir(plugin_dir)
			if not os.path.isdir(plugin_dir):
				return None
			rules_xml = SqUtils.get_file('rules.xml', plugin_dir)
			if os.path.isfile(rules_xml):
				return plugin_dir
			pom_xml = SqUtils.get_file('pom.xml', plugin_dir)
			if not os.path.isfile(pom_xml):
				return None
			parser = etree.XMLParser(recover=True)
			xtree = etree.parse(pom_xml, parser)
			xroot = xtree.getroot()
			if xroot is None:
				return None
			xnode = xroot.find('{*}artifactId')
			if xnode is None:
				return None
			artifact_name = xnode.text.strip()
			if artifact_name == 'sonar-findbugs-plugin':
				rules_dir = os.path.realpath(os.path.join(plugin_dir, 'src', 'main', 'resources', 'org', 'sonar', 'plugins', 'findbugs'))
				return SonarQube.Rules.find_dir(rules_dir)
			else:
				return None
		
		@classmethod
		def parse(cls, rules_xml):
			rules_xml = SqUtils.get_file(rules_xml)
			if not os.path.isfile(rules_xml):
				raise Exception('"%s" does not exist' % rules_xml)
			xtree = etree.parse(rules_xml)
			xroot = xtree.getroot()
			
			rules = cls()
			for xrule in xroot.iterfind('rule'):
				rule = SonarQube.Rule.parse(xrule)
				if rule:
					rules[rule.key] = rule
			return rules
	
	class Rule(object):
		def __init__(self, key, config_key, priority, status, cardinality, name, description):
			self.__key = key
			self.__config_key = config_key if config_key else key
			self.__priority = SonarQube.RulePriority.get(priority)
			self.__status = SonarQube.RuleStatus.get(status)
			self.__cardinality = cardinality
			self.__name = name
			self.__description = description
			self.__tags = []
			self.__params = {}
			self.__index = 0
		
		@property
		def key(self):
			return self.__key
		
		@property
		def config_key(self):
			return self.__config_key
		
		@property
		def priority(self):
			return self.__priority
		
		@property
		def status(self):
			return self.__status
		
		@property
		def cardinality(self):
			return self.__cardinality
		
		@property
		def name(self):
			return self.__name
		
		@property
		def description(self):
			return self.__description
		
		@property
		def tags(self):
			return self.__tags
		
		@property
		def params(self):
			return self.__params
		
		@property
		def index(self):
			return self.__index
		
		@classmethod
		def parse(cls, xrule):
			key = SqXml.get_attr_value(xrule, 'key')
			v = SqXml.get_cnode_text(xrule, 'key')
			if v and not key: key = v
			if not key: return None
			priority = SqXml.get_attr_value(xrule, 'priority')
			v = SqXml.get_cnode_text(xrule, 'priority')
			if v and not priority: priority = v
			config_key = SqXml.get_cnode_text(xrule, 'configKey')
			status = SqXml.get_cnode_text(xrule, 'status')
			cardinality = SqXml.get_cnode_text(xrule, 'cardinality')
			name = SqXml.get_cnode_text(xrule, 'name')
			description = SqXml.get_cnode_text(xrule, 'description')
			tags = []
			for xtag in SqXml.get_nodes(xrule, 'tag'):
				v = SqXml.get_node_text(xtag)
				if v: tags.append(v)
			params = {}
			for xparam in SqXml.get_nodes(xrule, 'param'):
				param = SonarQube.RuleParam.parse(xparam)
				if param: params[param.key] = param
			index = xrule.getparent().index(xrule)
			rule = cls(key, config_key, priority, status, cardinality, name, description)
			rule.__tags = tags
			rule.__params = params
			rule.__index = index + 1
			return rule
		
		def __repr__(self):
			attr = '%s' % (self.key)
			attr += ', priority=%s' % (self.priority)
			if self.status != SonarQube.RuleStatus.DEFAULT:
				attr += ', status=%s' % (self.status)
			return "Rule(%s)" % attr
	
	class RuleParam(object):
		def __init__(self, key, ptype, description, default_value):
			self.__key = key
			self.__ptype = SonarQube.PropertyType.get(ptype)
			self.__description = description
			self.__default_value = default_value
		
		@property
		def key(self):
			return self.__key
		
		@property
		def ptype(self):
			return self.__ptype
		
		@property
		def description(self):
			return self.__description
		
		@property
		def default_value(self):
			return self.__default_value
		
		@classmethod
		def parse(cls, xparam):
			key = SqXml.get_attr_value(xparam, 'key')
			v = SqXml.get_cnode_text(xparam, 'key')
			if v and not key: key = v
			if not key: return None
			ptype = SqXml.get_attr_value(xparam, 'type')
			v = SqXml.get_cnode_text(xparam, 'type')
			if v and not ptype: ptype = v
			description = SqXml.get_cnode_text(xparam, 'description')
			default_value = SqXml.get_cnode_text(xparam, 'defaultValue') or None
			param = cls(key, ptype, description, default_value)
			return param
	
	class RulePriority(object):
		DEFAULT = 'INFO'
		ALL = ['BLOCKER', 'CRITICAL', 'MAJOR', 'MINOR', 'INFO']
		
		@classmethod
		def get(cls, priority):
			if priority is not None: 
				priority = priority.upper()
				if priority in cls.ALL:
					return priority
			return cls.DEFAULT
		
		@classmethod
		def get_level(cls, priority):
			try:
				return cls.ALL.index(priority)
			except:
				priority = cls.get(priority)
				return cls.get_level(priority)
	
	class RuleStatus(object):
		DEFAULT = 'READY'
		ALL = ['READY', 'BETA', 'DEPRECATED', 'REMOVED']
		
		@classmethod
		def get(cls, status):
			if status is not None: 
				status = status.upper()
				if status in cls.ALL:
					return status
			return cls.DEFAULT
		
		@classmethod
		def get_level(cls, status):
			try:
				return cls.ALL.index(status)
			except:
				status = cls.get(status)
				return cls.get_level(status)

	class PropertyType(object):
		DEFAULT = 'STRING'
		ALL = ['STRING', 'TEXT', 'PASSWORD', 'BOOLEAN', 'INTEGER', 'FLOAT', 
		       'METRIC', 'LICENSE', 'REGULAR_EXPRESSION', 'PROPERTY_SET']
		OLD = {'I': 'INTEGER', 'S': 'STRING', 'B': 'BOOLEAN', 'R': 'REGULAR_EXPRESSION'}
		
		@classmethod
		def get(cls, ptype):
			if ptype is not None:
				ptype = ptype.upper()
				if ptype == 'I{}': return 'i{}'
				if ptype == 'S{}': return 's{}'
				if ptype in cls.OLD:
					return cls.OLD[ptype]
				if ptype in cls.ALL:
					return ptype
			return cls.DEFAULT
	
	class RuleProfile(object):
		@staticmethod
		def find_dir(plugin_dir):
			return SonarQube.Rules.find_dir(plugin_dir)
	
	class RuleProperties(object):
		@staticmethod
		def find_dir(plugin_dir):
			rules_dir = SonarQube.Rules.find_dir(plugin_dir)
			if rules_dir is None:
				return None
			
			return os.path.realpath(os.path.join(rules_dir, '..', '..', 'l10n'))
