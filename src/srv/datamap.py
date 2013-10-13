#! /usr/bin/python
# -*- coding: iso-8859-15 -*-
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

from collections import namedtuple
from frames import *

# 'param' type is for setting values that can be read and written
# 'data' type is for read-only measurement values
# 'command' type is for write-only data
param   = namedtuple('param',   'frame index decimals address min max')
data    = namedtuple('data',    'frame index decimals')
command = namedtuple('command', 'address min max')

# dataBaseMap is a dictionary of parameter names and their protocol mappings.
# The protocol mapping is itself a dictionary with "supported from" and "support ends with" version strings
# as key and a "param, data or command" named tuple as value. This way a parameter name can have
# several different protocol mappings identified by their version identifiers.
# All chip versions, existing and future, are newer than '0000' and older than 'zzzz'
# 'data' type is for read-only measurement values
# 'param' type is for setting values that can be read and written
# 'command' type is for write-only data

dataBaseMap =  {

#    parameter name             versions        type   frame   index decimals
    'power':                { ('0000','zzzz') : data (FrameZ00,  0,     0) }, # Z00 is probably supported on all version
    'power_kW':             { ('0000','zzzz') : data (FrameZ00,  1,     1) },
    'boiler_temp':          { ('0000','zzzz') : data (FrameZ00,  2,     1) },
    'chute_temp':           { ('0000','zzzz') : data (FrameZ00,  3,     0) },
    'smoke_temp':           { ('0000','zzzz') : data (FrameZ00,  4,     0) },
    'oxygen':               { ('0000','zzzz') : data (FrameZ00,  5,     1) },
    'light':                { ('0000','zzzz') : data (FrameZ00,  6,     0) },
    'feeder_time':          { ('0000','zzzz') : data (FrameZ00,  7,     0) },
    'ignition_time':        { ('0000','zzzz') : data (FrameZ00,  8,     0) },
    'alarm':                { ('0000','zzzz') : data (FrameZ00,  9,     0) },
    'oxygen_desired':       { ('0000','zzzz') : data (FrameZ00, 11,     1) },
    'mode':                 { ('0000','zzzz') : data (FrameZ00, 16,     0) },
    'model':                { ('0000','zzzz') : data (FrameZ00, 17,     0) },
    'motor_time':           { ('0000','zzzz') : data (FrameZ02,  0,     0) },
    'el_time':              { ('0000','zzzz') : data (FrameZ02,  1,     0) },
    'motor_time_perm':      { ('0000','zzzz') : data (FrameZ02,  2,     0) },
    'el_time_perm':         { ('0000','zzzz') : data (FrameZ02,  3,     0) },
    'ignition_count':       { ('4.99','zzzz') : data (FrameZ03,  8,     0) },
    'boiler_return_temp':   { ('6.03','zzzz') : data (FrameZ06,  0,     0) },
    'hotwater_temp':        { ('6.03','zzzz') : data (FrameZ06,  1,     0) },
    'outside_temp':         { ('6.03','zzzz') : data (FrameZ06,  2,     0) },
    'indoor_temp':          { ('6.03','zzzz') : data (FrameZ06,  3,     0) },
    'flow':                 { ('6.03','zzzz') : data (FrameZ06,  4,     0) },
    'version':              { ('0000','zzzz') : data (FrameZ04,  1,    -1) }, # decimals = -1 means that this is a string, not a number

#    parameter name             versions        type   frame    index  dec    addr   min    max
    'blower_low':           { ('4.99','zzzz') : param (FrameZ01,  0,    0,    'A00',   4,    50) },
    'blower_high':          { ('4.99','zzzz') : param (FrameZ01,  1,    0,    'A01',   5,   100) },
    'blower_mid':           { ('4.99','zzzz') : param (FrameZ03, 14,    0,    'A06',   5,    75) },
    'blower_cleaning':      { ('4.99','zzzz') : param (FrameZ01,  4,    0,    'A04',  25,   200) },
    'boiler_temp_set':      { ('0000','zzzz') : param (FrameZ00, 10,    0,    'B01',  40,    85) },
    'boiler_temp_min':      { ('4.99','zzzz') : param (FrameZ01,  9,    0,    'B03',  10,    70) },
    'feeder_low':           { ('4.99','zzzz') : param (FrameZ01, 10,    2,    'B04',   0.5,  25) },
    'feeder_high':          { ('4.99','zzzz') : param (FrameZ01, 11,    1,    'B05',   1,   100) },
    'feed_per_minute':      { ('4.99','zzzz') : param (FrameZ01, 12,    0,    'B06',   1,     3) },

    'boiler_temp_diff_down':{ ('4.99','zzzz') : param (FrameZ01, 17,    0,    'C03',   0,    20) },
    'boiler_temp_diff_up':  { ('4.99','zzzz') : param (FrameZ03, 13,    0,    'C04',   0,    15) },

    'light_required':       { ('4.99','zzzz') : param (FrameZ01, 22,    0,    'D03',   0,   100) },

    'oxygen_regulation':    { ('4.99','zzzz') : param (FrameZ01, 23,    0,    'E00',   0,     2) },
    'oxygen_low':           { ('4.99','zzzz') : param (FrameZ01, 24,    1,    'E01',  10,    19) },
    'oxygen_high':          { ('4.99','zzzz') : param (FrameZ01, 25,    1,    'E02',   2,    12) },
    'oxygen_mid':           { ('6.50','zzzz') : param (FrameZ08, 7,     1,    'E06',   0,    21) },
    'oxygen_gain':          { ('4.99','zzzz') : param (FrameZ01, 26,    2,    'E03',   0,    99.99) },

    'feeder_capacity_min':  { ('4.99','zzzz') : param (FrameZ01, 27,    0,    'F00', 400,  2000) },
    'feeder_capacity':      { ('0000','zzzz') : param (FrameZ00, 12,    0,    'F01', 400,  8000) },
    'feeder_capacity_max':  { ('4.99','zzzz') : param (FrameZ01, 29,    0,    'F02', 400,  8000) },

#    parameter name             versions        type   frame    index  dec    addr   min    max
    'chimney_draught':      { ('0000','6.85') : param (FrameZ00, 13,    0,    'G00',   0,    10) },
    'chute_temp_max':       { ('4.99','zzzz') : param (FrameZ01, 31,    0,    'G01',  50,    90) },
    'regulator_P':          { ('4.99','zzzz') : param (FrameZ01, 32,    1,    'G02',   1,    20) },
    'regulator_I':          { ('4.99','zzzz') : param (FrameZ01, 33,    2,    'G03',   0,     5) },
    'regulator_D':          { ('4.99','zzzz') : param (FrameZ01, 34,    1,    'G04',   1,    50) },
    'blower_corr_low':      { ('4.99','zzzz') : param (FrameZ01, 39,    0,    'G05',  50,   150) },
    'blower_corr_high':     { ('4.99','zzzz') : param (FrameZ01, 40,    0,    'G06',  50,   150) },
    'cleaning_interval':    { ('4.99','zzzz') : param (FrameZ01, 41,    0,    'G07',   1,   120) },
    'cleaning_time':        { ('4.99','zzzz') : param (FrameZ01, 42,    0,    'G08',   0,    60) },
    'language':             { ('0000','zzzz') : param (FrameZ04, 0,     0,    'G09',   0,     3) },

    'autocalculation':      { ('4.99','zzzz') : param (FrameZ03, 10,    0,    'H04',   0,     1) },
    'time_minutes':         { ('4.99','zzzz') : param (FrameZ01, 44,    0,    'H07',   0,  1439) },

    'oxygen_corr_10':       { ('4.99','zzzz') : param (FrameZ03, 1,     0,    'I00',   0,   100) },
    'oxygen_corr_50':       { ('4.99','zzzz') : param (FrameZ03, 2,     0,    'I01',   0,   100) },
    'oxygen_corr_100':      { ('4.99','zzzz') : param (FrameZ03, 3,     0,    'I02',   0,   100) },
    'oxygen_corr_interval': { ('4.99','zzzz') : param (FrameZ03, 4,     0,    'I03',   1,    60) },
    'oxygen_regulation_P':  { ('4.99','zzzz') : param (FrameZ03, 5,     2,    'I04',   0,     5) },
    'oxygen_regulation_D':  { ('4.99','zzzz') : param (FrameZ03, 6,     0,    'I05',   0,   100) },
    'blower_off_time':      { ('4.99','zzzz') : param (FrameZ03, 9,     0,    'I07',   0,    30) },

    'timer_heating_period': { ('6.03','zzzz') : param (FrameZ05, 9, 	0,    'K00',   0,  1440) },
    'timer_hotwater_period':{ ('6.03','zzzz') : param (FrameZ05, 10, 	0,    'K01',   0,  1440) },
    'timer_heating_start_1':{ ('6.03','zzzz') : param (FrameZ05, 11, 	0,    'K02',   0,  1439) },
    'timer_heating_start_2':{ ('6.03','zzzz') : param (FrameZ05, 12, 	0,    'K03',   0,  1439) },
    'timer_heating_start_3':{ ('6.03','zzzz') : param (FrameZ05, 13, 	0,    'K04',   0,  1439) },
    'timer_heating_start_4':{ ('6.03','zzzz') : param (FrameZ05, 14, 	0,    'K05',   0,  1439) },
    'timer_hotwater_start_1':{('6.03','zzzz') : param (FrameZ05, 15, 	0,    'K06',   0,  1439) },
    'timer_hotwater_start_2':{('6.03','zzzz') : param (FrameZ05, 16, 	0,    'K07',   0,  1439) },
    'timer_hotwater_start_3':{('6.03','zzzz') : param (FrameZ05, 17, 	0,    'K08',   0,  1439) },
    'magazine_content'      :{('6.03','zzzz') : param (FrameZ05, 25,    0,    'F04',   0,  9999) },

    'comp_clean_interval':  { ('6.03','zzzz') : param (FrameZ05, 18,    0,    'L00',   0,   999) },
    'comp_clean_time':      { ('6.03','6.69') : param (FrameZ05, 19,    0,    'L01',   0,    10) },
    'comp_clean_time':      { ('6.69','zzzz') : param (FrameZ05, 19,    1,    'L01',   1,   900) },
    'comp_clean_blower':    { ('6.03','zzzz') : param (FrameZ05, 20,    0,    'L02',   0,   100) },
    'comp_clean_wait':      { ('6.12','6.69') : param (FrameZ05, 29,    0,    'L03',   0,   300) },
    'comp_clean_wait':      { ('6.69','zzzz') : param (FrameZ05, 29,    0,    'L03',   0,   900) },

    'blower_corr_mid':      { ('4.99','zzzz') : param (FrameZ05, 21,    0,    'M00',  50,   150) },

#    parameter name             versions        type   frame    index  dec    addr   min    max
    'min_power':            { ('4.99','zzzz') : param (FrameZ01, 37,    0,    'H02',  10,   100) },
    'max_power':            { ('4.99','zzzz') : param (FrameZ01, 38,    0,    'H03',  10,   100) },

    'burner_off':           { ('4.99','zzzz') : command (                     'V00',   0,     0) },
    'burner_on':            { ('4.99','zzzz') : command (                     'V01',   0,     0) },
    'reset_alarm':          { ('4.99','zzzz') : command (                     'V02',   0,     0) },
}
