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

dataEnumerations = {
   # name,              enumeration
    'alarm':          ('ok',
                       'Low boiler temperature',
                       'Ignition failed',
                       'Max chute temperature exceeded',
                       'Boiler temperature sensor error',
                       'Light sensor error',
                       'Chute temperature sensor error',
                       'No fire',
                       'Motor output error'),

    'mode':           ('Waiting', 
                       'Waiting_', 
                       'Starting 1', 
                       'Starting 1_', 
                       'Starting 2', 
                       'Running', 
                       'Paused', 
                       'Making hotwater', 
                       'Error - Low boiler temperature',
                       'Stopped',
                       'Summer stop',
                       'Error - Temperature sensor hot',
                       'Burner connector plug removed',
                       'Error - Ignition fail',
                       'Shut off',
                       'Error - Boiler sensor',
                       'Error - Light sensor',
                       'Error - Chute temperature sensor',
                       '',  
                       'Error - Motor output',
                       'Running on battery'),
                       
    'model':          ('Boink',
                       'Scotte',
                       'Biocomfort/Woody with autocalc',
                       'Biocomfort/Woody without autocalc'),
}

