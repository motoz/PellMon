#! /usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
    Copyright ('', '',  ''),C) 2013  Anders Nylund

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    ('', '',  ''),at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

dataEnumerations = {          #name, enumeration
    'alarm':          ('no alarm',
                       'Low boiler temperature',
                       'Ignition failed',
                       'Max chute temperature exceeded',
                       'Boiler temperature sensor error',
                       'Light sensor error',
                       'Chute temperature sensor error',
                       'No fire',
                       'Motor output error'),

    'mode':           ('Waiting', 
                       '', 
                       'Starting 1', 
                       '', 
                       'Starting 2', 
                       'Running', 
                       'Pause', 
                       'Hotwater', 
                       'Error - Low boiler temperature'
                       'Stopped',
                       'Summer stop',
                       'Error - temperature sensor hot',
                       'Burner connector plug removed',
                       'Error - Ignition fail',
                       'No fire',
                       'Error - boiler sensor',
                       'Error - light sensor',
                       'Error - chute temperature sensor',
                       '',  
                       'Error - motor output',
                       'Running on battery'),
                       
    'model':          ('Boink',
                       'Scotte',
                       'Biocomfort/Woody with autocalc',
                       'Biocomfort/Woody without autocalc'),
}   

