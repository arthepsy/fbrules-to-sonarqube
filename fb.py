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

class FbXml():
	@staticmethod
	def get_attr_value(xnode, attr_name):
		return (xnode.get(attr_name) or '').strip()
	
	@staticmethod
	def get_node(xnode, child_name):
		return xnode.find('{*}' + child_name)
	
	@staticmethod
	def get_node_text(xnode, default_value=None, clean=False):
		if xnode is not None and xnode.text is not None:
			value = xnode.text.strip()
		else:
			value = ''
		if len(value) == 0 and default_value is not None:
			value = default_value
		return FbUtils.get_clean(value) if clean else value
	
	@staticmethod
	def get_cnode_text(xnode, child_name, default_value=None, clean=False):
		xnode = FbXml.get_node(xnode, child_name)
		return FbXml.get_node_text(xnode, default_value, clean)
	
class FbUtils():
	@staticmethod
	def parse_int(s):
		return int(FbUtils.parse_num(s))
	
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
			return FbUtils.parse_dec(s)
	
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
			root = FbUtils.get_dir(root)
			p = os.path.join(root, p)
		return os.path.realpath(p)

class FindBugsPlugin():
	def __init__(self, head, categories, patterns, codes):
		self.head = head
		self.categories = categories
		self.patterns = patterns
		self.codes = codes
		self.ranker = FindBugsPlugin.BugRanker()
	
	@staticmethod
	def parse(etc_dir):
		etc_dir = FbUtils.get_dir(etc_dir)
		if not os.path.isdir(etc_dir):
			raise Exception('"%s" does not exist' % etc_dir)
		findbugs_xml = FbUtils.get_file('findbugs.xml', etc_dir)
		messages_xml = FbUtils.get_file('messages.xml', etc_dir)
		if not os.path.isfile(findbugs_xml):
			raise Exception('"%s" does not exist' % findbugs_xml)
		if not os.path.isfile(messages_xml):
			raise Exception('"%s" does not exist' % messages_xml)
		
		plg_xtree = etree.parse(findbugs_xml)
		plg_xroot = plg_xtree.getroot()
		
		msg_xtree = etree.parse(messages_xml)
		msg_xroot = msg_xtree.getroot()
		
		head = FindBugsPlugin.Head.parse(plg_xtree, msg_xtree)
		
		categories = {}
		for xcat in plg_xtree.xpath('/FindbugsPlugin/BugCategory'):
			cat_name = FbXml.get_attr_value(xcat, 'category')
			if not cat_name: continue
			if cat_name in categories: continue
			is_hidden = (FbXml.get_attr_value(xcat, 'hidden').lower() == 'true')
			category = FindBugsPlugin.BugCategory(cat_name)
			category.is_hidden = is_hidden
			categories[cat_name] = category
			
		for xcat in msg_xtree.xpath('/MessageCollection/BugCategory'):
			cat_name = FbXml.get_attr_value(xcat, 'category')
			if not cat_name: continue
			if cat_name in categories:
				category = categories[cat_name]
			else:
				category = FindBugsPlugin.BugCategory(cat_name)
			abbr = FbXml.get_cnode_text(xcat, 'Abbreviation')
			description = FbXml.get_cnode_text(xcat, 'Description')
			details = FbXml.get_cnode_text(xcat, 'Details', clean=True)
			if abbr: category.abbr = abbr
			if description: category.description = description
			if details: category.details = details
			categories[cat_name] = category
		
		patterns = {}
		for plg_xbp in plg_xtree.xpath('/FindbugsPlugin/BugPattern'):
			bp_name = FbXml.get_attr_value(plg_xbp, 'type')
			if not bp_name: continue
			bp_abbr = FbXml.get_attr_value(plg_xbp, 'abbrev')
			bp_cat_name = FbXml.get_attr_value(plg_xbp, 'category')
			bp_cweid = FbUtils.parse_int(FbXml.get_attr_value(plg_xbp, 'cweid'))
			bp_is_exp = (FbXml.get_attr_value(plg_xbp, 'experimental').lower() == 'true')
			bp_is_old = (FbXml.get_attr_value(plg_xbp, 'deprecated').lower() == 'true')
			
			msg_xbp = msg_xtree.xpath('/MessageCollection/BugPattern[@type="%s"]' % bp_name)
			if len(msg_xbp) != 1:
				raise Exception('could not find message for bug pattern "%s"' % bp_name)
			xmsg = msg_xbp[0]
			bp_short_desc = FbXml.get_cnode_text(xmsg, 'ShortDescription', clean=True)
			bp_long_desc = FbXml.get_cnode_text(xmsg, 'LongDescription', clean=True)
			bp_details = FbXml.get_cnode_text(xmsg, 'Details')
			
			pattern = FindBugsPlugin.BugPattern(bp_name, bp_abbr, bp_cat_name, bp_is_exp, bp_short_desc, bp_long_desc, bp_details, bp_cweid)
			pattern.is_deprecated = bp_is_old
			patterns[bp_name] = pattern
		
		codes = {}
		for msg_xbc in msg_xtree.xpath('/MessageCollection/BugCode'):
			bc_name = FbXml.get_attr_value(msg_xbc, 'abbrev')
			if not bc_name: continue
			if bc_name in codes: continue
			bc_desc = FbXml.get_node_text(msg_xbc)
			plg_xbc = plg_xtree.xpath('/FindbugsPlugin/BugCode[@abbrev="%s"]' % bc_name)
			if len(plg_xbc) == 1:
				bc_cweid = FbUtils.parse_int(FbXml.get_attr_value(plg_xbc[0], 'cweid'))
			else:
				bc_cweid = 0
			code = FindBugsPlugin.BugCode(bc_name, bc_desc, bc_cweid)
			codes[bc_name] = code
		
		plugin = FindBugsPlugin(head, categories, patterns, codes)
		bugrank_file = FbUtils.get_file('bugrank.txt', etc_dir)
		if os.path.isfile(bugrank_file):
			plugin.load_ranker(etc_dir)
		return plugin
	
	def load_ranker(self, rank_dir):
		self.ranker = FindBugsPlugin.BugRanker.parse(rank_dir)
	
	def __repr__(self):
		attr = '%s' % (self.head.short_id)
		attr += ', categories=%d' % len(self.categories)
		attr += ', patterns=%d' % len(self.patterns)
		attr += ', codes=%d' % len(self.codes)
		return "FindBugsPlugin(%s)" % attr
	
	class Head():
		def __init__(self, plugin_id, provider, website, description, details):
			self.short_id = self._get_short_id(plugin_id)
			self.plugin_id = plugin_id
			self.provider = provider
			self.website = website
			self.description = description
			self.details = details
		
		def _get_short_id(self, plugin_id):
			dot = plugin_id.rindex('.')
			if dot > 0:
				short_id = plugin_id[dot+1:]
			else:
				short_id = plugin_id
			return short_id
		
		def __repr__(self):
			attr = '%s, plugin_id=%s' % (self.short_id, self.plugin_id)
			if self.provider: attr += ', provider="%s"' % self.provider
			if self.description: attr += ', description="%s"' % self.description
			return "Head(%s)" % (attr)

		@staticmethod
		def parse(plg_xtree, msg_xtree):
			xroot = plg_xtree.getroot()
			plugin_id = FbXml.get_attr_value(xroot, 'pluginid')
			if not plugin_id:
				raise Exception('pluginid attribute not found in root node')
			provider = FbXml.get_attr_value(xroot, 'provider')
			website = FbXml.get_attr_value(xroot, 'website')
			xplugins = msg_xtree.xpath('/MessageCollection/Plugin')
			if len(xplugins) != 1:
				raise Exception('could not find plugin description')
			xplugin = xplugins[0]
			description = FbXml.get_cnode_text(xplugin, 'ShortDescription', clean=True)
			details = FbXml.get_cnode_text(xplugin, 'Details')
			head = FindBugsPlugin.Head(plugin_id, provider, website, description, details)
			return head
	
	class BugCategory():
		def __init__(self, name, abbr=None, description=None, details=None):
			self.is_hidden = False
			self.name = name
			self.abbr = abbr
			self.description = description
			self.details = details
		
		def __repr__(self):
			attr = '%sname=%s' % ('hidden, ' if self.is_hidden else '', self.name)
			if self.abbr: attr += ', abbr=%s' % self.abbr
			if self.description: attr += ', description="%s"' % self.description
			return "BugCategory(%s)" % (attr)
	
	class BugPattern():
		def __init__(self, name, abbr, category_name, is_experimental, short_desc, long_desc, details, cweid):
			self.name = name
			self.abbr = abbr
			self.category_name = category_name
			self.is_experimental = is_experimental
			self.is_deprecated = False
			self.short_desc = short_desc
			self.long_desc = long_desc
			self.details = details
			self.cweid = cweid
		
		def get_rank(self, rankers):
			return FindBugsPlugin.BugRanker.rank_pattern(self, rankers)
		
		def __repr__(self):
			attr = 'name=%s' % self.name
			if self.abbr: attr += ', abbr=%s' % self.abbr
			if self.category_name: attr += ', category=%s' % self.category_name
			if self.short_desc: attr += ', short_desc="%s"' % self.short_desc
			return "BugPattern(%s)" % (attr)
	
	class BugCode():
		def __init__(self, name, description, cweid):
			self.name = name
			self.description = description
			self.cweid = cweid
		
		def __repr__(self):
			attr = 'name=%s' % self.name
			if self.description: attr += ', description=%s' % self.description
			if self.cweid > 0: attr += ', cweid=%d' % self.cweid
			return "BugCode(%s)" % (attr)
	
	class BugPriority():
		HIGH = 0
		LOW = 5
		NORMAL = 2
		DEFAULT = 10
		EXPERIMENTAL = 4
		IGNORE = 5
	
	class BugRanker():
		def __init__(self, patterns = None, kinds = None, categories = None):
			self.patterns = patterns or FindBugsPlugin.BugRanker.Scorer()
			self.kinds = kinds or FindBugsPlugin.BugRanker.Scorer()
			self.categories = categories or FindBugsPlugin.BugRanker.Scorer()
		
		@staticmethod
		def _get_priority(pattern):
			if pattern.is_experimental:
				return FindBugsPlugin.BugPriority.EXPERIMENTAL
			return FindBugsPlugin.BugPriority.HIGH
		
		@staticmethod
		def _adjust_prio(priority):
			return priority
		
		@staticmethod
		def _adjust_rank(rank, priority):
			"""ranks: 1-4=scariest, 5-9=scary, 10-14=troubling, 15+=of concern"""
			priority = FindBugsPlugin.BugRanker._adjust_prio(priority)
			return max(1, min(rank + priority, 20))
		
		@staticmethod
		def rank_pattern(pattern, rankers):
			rank = 0
			for r in rankers:
				if not r: continue
				rank += r.patterns.get(pattern.name)
				if not r.patterns.is_relative(pattern.name):
					return rank
			for r in rankers:
				if not r: continue
				rank += r.kinds.get(pattern.abbr)
				if not r.kinds.is_relative(pattern.abbr):
					return rank
			for r in rankers:
				if not r: continue
				rank += r.categories.get(pattern.category_name)
				if not r.categories.is_relative(pattern.category_name):
					return rank
			priority = FindBugsPlugin.BugRanker._get_priority(pattern)
			return FindBugsPlugin.BugRanker._adjust_rank(rank, priority)
		
		@staticmethod
		def parse(rank_dir):
			rank_dir = FbUtils.get_dir(rank_dir)
			if not os.path.isdir(rank_dir):
				raise Exception('"%s" does not exist' % rank_dir)
			bugrank_path = FbUtils.get_file('bugrank.txt', rank_dir)
			adjust_bugrank_path = FbUtils.get_file('adjustBugrank.txt', rank_dir)
			if not os.path.isfile(bugrank_path):
				raise Exception('"%s" does not exist' % bugrank_path)
			#if not os.path.isfile(adjust_bugrank_path):
			#	raise Exception('"%s" does not exist' % adjust_bugrank_path)
			
			patterns = FindBugsPlugin.BugRanker.Scorer()
			kinds = FindBugsPlugin.BugRanker.Scorer()
			categories = FindBugsPlugin.BugRanker.Scorer()
			
			f = open(bugrank_path, 'r')
			for line in f:
				line = line.strip()
				if len(line) == 0 or line.startswith('#'): 
					continue
				parts = line.split(' ')
				if len(parts) != 3:
					continue
				rank = parts[0]
				kind = parts[1]
				what = parts[2]
				if kind == 'BugPattern':
					patterns.store(what, rank)
				elif kind == 'BugKind':
					kinds.store(what, rank)
				elif kind == 'Category':
					categories.store(what, rank)
			f.close()
			
			ranker = FindBugsPlugin.BugRanker(patterns, kinds, categories)
			return ranker
		
		def __repr__(self):
			attr = 'patterns=%d, kinds=%d, categories=%d' % (len(self.patterns), len(self.kinds), len(self.categories))
			return "BugRanker(%s)" % attr
		
		class Scorer():
			def __init__(self):
				self._adjustment = {}
				self._relative = {}
				pass
			
			def get(self, key):
				return self._adjustment[key] if key in self._adjustment else 0
			
			def is_relative(self, key):
				return key not in self._adjustment or key in self._relative
			
			def store(self, key, value):
				for k in key.split(','):
					if len(k) == 0: continue
					c = value[0]
					if c == '+' or c == '-':
						self._relative[k] = True
					v = FbUtils.parse_int(value)
					self._adjustment[k] = v
			
			def __len__(self):
				return len(self._adjustment)
