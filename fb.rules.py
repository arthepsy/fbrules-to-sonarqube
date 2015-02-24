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
		max_key_len = max(max_key_len, len(key))
		max_cat_len = max(max_cat_len, len(pattern.category_name))
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
		_out(fmt.format(ranked['rank'], ranked['priority'], p.category_name, p.name, p.short_desc))

def extract(fb_plugin_dir, sq_plugin_dir):
	fb_etc_dir = FindBugsPlugin.find_conf_dir(fb_plugin_dir)
	if fb_etc_dir is None:
		raise click.UsageError('Invalid FindBugs plugin directory: %s ' % fb_plugin_dir)
	fb_plugin = FindBugsPlugin.parse(fb_etc_dir)
	plugin_id = fb_plugin.head.short_id
	if plugin_id not in ['core', 'fbcontrib', 'findsecbugs']:
		raise click.UsageError('Unknown FindBugs plugin: %s ' % fb_plugin.head.plugin_id)
	sq_rules_dir = SonarQube.Rules.find_dir(sq_plugin_dir)
	if sq_rules_dir is None:
		raise click.UsageError('Invalid SonarQube plugin directory: %s ' % fb_plugin_dir)
	
	sq_rules_file = SonarQube.Rules.get_file(sq_rules_dir, fb_plugin.head.short_id)
	sq_profile_dir = sq_rules_dir
	sq_ruleprop_dir = os.path.realpath(os.path.join(sq_rules_dir, '..', '..', 'l10n'))
	sq_rulehtml_dir = os.path.realpath(os.path.join(sq_ruleprop_dir, 'findbugs', 'rules', 'findbugs'))
	
	sq_profile_file = None
	sq_ruleprop_file = None
	if plugin_id == 'core':
		sq_profile_file = os.path.join(sq_rules_dir, 'profile-findbugs.xml')
		sq_ruleprop_file = os.path.join(sq_ruleprop_dir, 'findbugs.properties')
	
	sq_rules = SonarQube.Rules.parse(sq_rules_file, sq_ruleprop_file, sq_rulehtml_dir)
	if sq_profile_file is not None and os.path.isfile(sq_profile_file):
		sq_profile = SonarQube.RulesProfile.parse(sq_profile_file)
	else:
		sq_profile = None
	
	_out('# rule_key:sq_rule_nr:sq_prop_nr:sq_prof_nr:priority:status:reason:tags')
	for p in sorted(fb_plugin.patterns.values(), key=lambda p: p.name):
		sq_rule_nr = 0
		sq_prop_nr = 0
		sq_prof_nr = 0
		priority = '?'
		status = ''
		reason = ''
		tags = []
		
		reason_not_in_sonar = 'NotInSonarProfile'
		reason_by_findbugs = 'ByFindBugsPlugin'
		
		if p.is_deprecated:
			status = 'DEPRECATED'
			reason = reason_by_findbugs
		elif p.is_experimental:
			status = 'EXPERIMENTAL'
			reason = reason_by_findbugs
		
		found_in_sq = False
		if p.name in sq_rules:
			sq_rule = sq_rules[p.name]
			sq_rule_nr = sq_rule.pattern_index
			sq_prop_nr = sq_rule.properties_index
			priority = sq_rule.priority
			if len(status) > 0 and status != sq_rule.status:
				if sq_rule.status != 'READY':
					raise Exception('Mismatched rule state {0} (FindBugs) vs {1} (SonarQube)'.format(status, sq_rule.status))
			else:
				status = sq_rule.status
			tags = sq_rule.tags
			if status == 'DEPRECATED':
				if len(sq_rule.deprecated_by) > 0:
					reason = ','.join(sq_rule.deprecated_by)
			if sq_profile:
				if p.name in sq_profile:
					found_in_sq = True
					sq_prof_nr = sq_profile[p.name].index
		else:
			pass
			#raise Exception('Rule %s not found in SonarQube rules' % p.name)
		if not found_in_sq:
			if status == 'READY' or status == '':
				status = 'DISABLED'
				reason = reason_not_in_sonar
			elif status == 'DEPRECATED':
				status += ',DISABLED'
				if reason == reason_by_findbugs:
					reason += ',' + reason_not_in_sonar
			elif status == 'EXPERIMENTAL':
				status += ',DISABLED'
				reason += ',' + reason_not_in_sonar
			else:
				raise Exception('Unknown rule state: ' + status)
		
		if status == 'READY':
			status = ''
		
		output = '{0}:{1}:{2}:{3}:{4}:{5}:{6}:{7}'.format(p.name, sq_rule_nr, sq_prop_nr, sq_prof_nr, priority, status, reason, ','.join(tags))
		if output.endswith(':::'):
			output = output[:-1]
		_out(output)


class CmdLine():
	CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
	_type_dir = click.Path(exists=True, file_okay=False, dir_okay=True, readable=True, resolve_path=True)
	_type_rofile = click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True)
	_type_rwfile = click.Path(exists=False, file_okay=True, dir_okay=False, writable=True, resolve_path=True)
	
	@click.group(context_settings=CONTEXT_SETTINGS)
	def main():
		pass
	
	@main.command(context_settings=CONTEXT_SETTINGS, short_help='list rules (rank, priority, category, etc)')
	@click.argument('fb_plugin_dir', metavar='<fb_plugin_dir> ...', type=_type_dir, nargs=-1)
	@click.option('-s', metavar='<sq_plugin_dir>', type=_type_dir, required=False, help='SonarQube FindBugs plugin directory')
	@click.pass_context
	def list(ctx, fb_plugin_dir, s):
		"""List FindBugs rules with ranking, priority, category, etc.
		
		\b
		<fb_plugin_dir>         FindBug plugin directory [multiple]
		 """
		if not len(fb_plugin_dir) > 0:
			_err(ctx.get_help())
		fb_plugins = []
		for path in fb_plugin_dir:
			fb_etc_dir = FindBugsPlugin.find_conf_dir(path)
			if fb_etc_dir is None:
				raise click.UsageError('Invalid plugin directory: %s ' % path)
			fb_plugin = FindBugsPlugin.parse(fb_etc_dir)
			fb_plugins.append(fb_plugin)
		sq_rules = None
		if s is not None:
			sq_rules_dir = SonarQube.Rules.find_dir(s)
			sq_rules_file = SonarQube.Rules.get_file(sq_rules_dir, fb_plugin.head.short_id)
			sq_rules = SonarQube.Rules.parse(sq_rules_file)
		patterns = fb_plugins[-1].patterns
		rankers = [p.ranker for p in fb_plugins]
		output(patterns, rankers, sq_rules)
	
	@main.command(context_settings=CONTEXT_SETTINGS, short_help='extract rules to fb2sq data file')
	@click.argument('fb_plugin_dir', metavar='<fb_plugin_dir>', type=_type_dir)
	@click.argument('sq_plugin_dir', metavar='<sq_plugin_dir>', type=_type_dir)
	@click.pass_context
	def extract(ctx, fb_plugin_dir, sq_plugin_dir):
		"""Extract FindBugs rules to fb2sq format.
		
		\b
		<fb_plugin_dir>         FindBug plugin directory
		<sq_plugin_dir>         SonarQube FindBugs plugin directory
		 """
		extract(fb_plugin_dir, sq_plugin_dir)

if __name__ == '__main__':
	cmd = CmdLine()
	cmd.main()
