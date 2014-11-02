#! /usr/bin/python
# -*- coding: utf-8 -*-
"""
    Copyright (C) 2013  Anders Nylund

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
class minutes_to_time:
    def decode(self, data):
        try:
            minutes = int(data)
            hours = minutes / 60
            minutes = minutes % 60
            return "%02u;%02u"%(hours, minutes)
        except:
            return data

    def encode(self, data):
        h,m = data.split(';')
        hours = int(h)
        minutes = int(m)
        return str(hours*60+minutes)

dataTransformations = {
   # name                tranformation functions
    'time_minutes':     minutes_to_time()
}



