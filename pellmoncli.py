#! /usr/bin/python
# -*- encoding: UTF-8 -*-

"""
    Copyright (C) 2013  Anders Nylund

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import dbus, readline, os
import sys

# Handles tab completion with input_raw
def complete(text, state):
	completerTexts=COMMANDS
	line = readline.get_line_buffer()
	splitline = line.split()
	if splitline:
		if line.startswith('get ') or line.startswith('g '):
			completerTexts=db
		elif line.startswith('set ') or line.startswith('s '):
			completerTexts=db
		else:
			completerTexts=COMMANDS
	for cmd in completerTexts:
		if cmd.startswith(text):
			if not state:
				return cmd+' '
			else:
				state -= 1

if __name__ == "__main__":

	# Connect to pellmonsrv on the dbus system bus
	bus = dbus.SystemBus()
	pelletService = bus.get_object('org.pellmon.int', '/org/pellmon/int')
	getItem = pelletService.get_dbus_method('GetItem', 'org.pellmon.int')
	setItem = pelletService.get_dbus_method('SetItem', 'org.pellmon.int')
	getdb = pelletService.get_dbus_method('GetDB', 'org.pellmon.int')
	
	# Get list of data/parameters
	db=getdb()

	run=True
	COMMANDS = ['get', 'set', 'quit']
	completerTexts=COMMANDS
	# Sets up readline for tab completion
	readline.parse_and_bind("tab: complete")
	readline.set_completer(complete)

	while run:
		try:
			a=raw_input(">")
			l=a.split()
			if len(l)==2:
				if l[0] in ['get', 'g']:
					if l[1] == "all":
						for item in db:
							try:
								print item, getItem(item)			
							except:
								pass
					else:
						if l[1] in db:
							try:
								print getItem(l[1])
							except dbus.exceptions.DBusException as e: 
								print "dbus error"
						else:
							print l[1]+" is not a data/parameter name "

			elif len(l)==3:
				if l[0] in ['set', 's']:
					if l[1] in db:
						print setItem(l[1], l[2])
					else:
						print l[1]+" is not a parameter/command name"

			elif len(l)==1:
				if l[0] in ['quit','q']:
					run=False
					
		except KeyboardInterrupt:
			run=False

