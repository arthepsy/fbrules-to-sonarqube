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
from __future__ import print_function
import sys, os, re, signal
import click
from lxml import etree

from fb import FindBugsPlugin
from sq import SonarQube

signal.signal(signal.SIGPIPE, signal.SIG_DFL)

def _err(*objs):
	print(*objs, file=sys.stderr)
	sys.exit(1)

def _out(*objs):
	print(*objs, file=sys.stdout)

def _file(p, root = None):
	if root is None:
		root = os.path.dirname(os.path.realpath(__file__))
	return os.path.realpath(os.path.join(root, p))

def _priority_sortlevel(priority):
	if priority == '-': return 100
	return SonarQube.RulePriority.get_level(priority)

def output(patterns, rankers, sq_rules = None):
	max_key_len = 1
	max_cat_len = 1
	ranks = {}
	for key, pattern in patterns.items():
		l = len(key)
		if l > max_key_len: max_key_len = l
		l = len(pattern.category)
		if l > max_cat_len: max_cat_len = l
		rank = pattern.get_rank(rankers)
		if sq_rules and pattern.name in sq_rules:
			priority = sq_rules[pattern.name].priority
		else:
			priority = '-'
		ranks[pattern.name] = {
			'rank': rank, 
			'priority': priority,
			'pattern': pattern
		}
	fmt = "{:<2} | {:<" + ('8' if sq_rules else '0') + "} | {:<" + str(max_cat_len) + "} | {:<" + str(max_key_len) + "} | {}"
	for k, ranked in sorted(ranks.items(), key=lambda i : (i[1].get('rank'), _priority_sortlevel(i[1].get('priority')))):
		p = ranked['pattern']
		_out(fmt.format(ranked['rank'], ranked['priority'], p.category, p.name, p.short_desc))

class CmdLine():
	_type_dir = click.Path(exists=True, file_okay=False, dir_okay=True, readable=True, resolve_path=True)
	_type_rofile = click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True)
	_type_rwfile = click.Path(exists=False, file_okay=True, dir_okay=False, writable=True, resolve_path=True)
	
	def run(self):
		self.rules()
	
	CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
	@click.command(context_settings=CONTEXT_SETTINGS)
	@click.argument('plugin_dir', metavar='<plugin_dir> ...', type=_type_dir, nargs=-1)
	@click.option('--rules', '-r', metavar='<rules>', type=_type_rofile, help='SonarQube rules.xml file')
	@click.pass_context
	def rules(ctx, plugin_dir, rules):
		"""List FindBugs rules with ranking, priority, category, etc.
		
		<plugin_dir>         FindBug plugin etc directory [multiple]
		 """
		if not len(plugin_dir) > 0:
			_err(ctx.get_help())
		fb_plugins = []
		for path in plugin_dir:
			fb_plugin = FindBugsPlugin.parse(path)
			if os.path.isfile(os.path.join(path, 'bugrank.txt')):
				fb_plugin.load_ranker(path)
			fb_plugins.append(fb_plugin)
		sq_rules = None
		if rules:
			sq_rules = SonarQube.Rules.parse(rules)
		patterns = fb_plugins[-1].patterns
		rankers = [p.ranker for p in fb_plugins]
		output(patterns, rankers, sq_rules)

if __name__ == '__main__':
	cmd = CmdLine()
	cmd.run()
