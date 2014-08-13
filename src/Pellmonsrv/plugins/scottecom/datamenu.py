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

# Tags:                       Basic  All      Settings   Measurements  Overview Blower Ignition Feeder Oxygen Timer Cleaning  Temps
dataBaseTags = {
    'power':                 ('X',   'X',      ' ',       'X',          'X',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'power_kW':              ('X',   'X',      ' ',       'X',          'X',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'boiler_temp':           ('X',   'X',      ' ',       'X',          'X',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     'X'),
    'chute_temp':            ('X',   'X',      ' ',       'X',          'X',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     'X'),
    'smoke_temp':            ('X',   'X',      ' ',       'X',          'X',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     'X'),
    'oxygen':                ('X',   'X',      ' ',       'X',          'X',     ' ',   ' ',     ' ',   'X',   ' ',  ' ',     ' '),
    'light':                 ('X',   'X',      ' ',       'X',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'feeder_time':           ('X',   'X',      ' ',       'X',          ' ',     ' ',   ' ',     'X',   ' ',   ' ',  ' ',     ' '),
    'ignition_time':         (' ',   'X',      ' ',       'X',          ' ',     ' ',   'X',     ' ',   ' ',   ' ',  ' ',     ' '),
    'alarm':                 ('X',   'X',      ' ',       ' ',          'X',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'oxygen_desired':        ('X',   'X',      ' ',       'X',          'X',     ' ',   ' ',     ' ',   'X',   ' ',  ' ',     ' '),
    'mode':                  ('X',   'X',      ' ',       ' ',          'X',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'model':                 ('X',   'X',      ' ',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'motor_time':            (' ',   'X',      ' ',       'X',          ' ',     ' ',   ' ',     'X',   ' ',   ' ',  ' ',     ' '),
    'el_time':               ('X',   'X',      ' ',       'X',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'motor_time_perm':       (' ',   'X',      ' ',       'X',          ' ',     ' ',   ' ',     'X',   ' ',   ' ',  ' ',     ' '),
    'el_time_perm':          (' ',   'X',      ' ',       'X',          ' ',     ' ',   ' ',     'X',   ' ',   ' ',  ' ',     ' '),
    'ignition_count':        ('X',   'X',      ' ',       'X',          'X',     ' ',   'X',     ' ',   ' ',   ' ',  ' ',     ' '),
    'boiler_return_temp':    ('X',   'X',      ' ',       'X',          'X',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     'X'),
    'hotwater_temp':         ('X',   'X',      ' ',       'X',          'X',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     'X'),
    'outside_temp':          ('X',   'X',      ' ',       'X',          'X',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     'X'),
    'indoor_temp':           ('X',   'X',      ' ',       'X',          'X',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     'X'),
    'flow':                  ('X',   'X',      ' ',       'X',          'X',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'version':               ('X',   'X',      ' ',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'blower_low':            ('X',   'X',      'X',       ' ',          ' ',     'X',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'blower_high':           ('X',   'X',      'X',       ' ',          ' ',     'X',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'blower_mid':            ('X',   'X',      'X',       ' ',          ' ',     'X',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'blower_cleaning':       ('X',   'X',      'X',       ' ',          ' ',     'X',   ' ',     ' ',   ' ',   ' ',  'X',     ' '),
    'boiler_temp_set':       ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     'X'),
    'boiler_temp_min':       (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     'X'),
    'feeder_low':            (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     'X',   ' ',   ' ',  ' ',     ' '),
    'feeder_high':           (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     'X',   ' ',   ' ',  ' ',     ' '),
    'feed_per_minute':       (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     'X',   ' ',   ' ',  ' ',     ' '),
    'boiler_temp_diff_up':   ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     'X'),
    'boiler_temp_diff_down': ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     'X'),
    'light_required':        (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'oxygen_regulation':     (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'oxygen_low':            ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   'X',   ' ',  ' ',     ' '),
    'oxygen_high':           ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   'X',   ' ',  ' ',     ' '),
    'oxygen_mid':            ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   'X',   ' ',  ' ',     ' '),
    'oxygen_gain':           (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   'X',   ' ',  ' ',     ' '),
    'feeder_capacity_min':   (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     'X',   ' ',   ' ',  ' ',     ' '),
    'feeder_capacity':       ('X',   'X',      'X',       'X',          ' ',     ' ',   ' ',     'X',   ' ',   ' ',  ' ',     ' '),
    'feeder_capacity_max':   (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     'X',   ' ',   ' ',  ' ',     ' '),
    'chimney_draught':       ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'chute_temp_max':        (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     'X'),
    'regulator_P':           (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'regulator_I':           (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'regulator_D':           (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'blower_corr_low':       ('X',   'X',      'X',       ' ',          ' ',     'X',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'blower_corr_high':      ('X',   'X',      'X',       ' ',          ' ',     'X',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'cleaning_interval':     ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  'X',     ' '),
    'cleaning_time':         ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  'X',     ' '),
    'language':              ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'autocalculation':       (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     'X',   ' ',   ' ',  ' ',     ' '),
    'time_minutes':          (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'oxygen_corr_10':        (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   'X',   ' ',  ' ',     ' '),
    'oxygen_corr_50':        (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   'X',   ' ',  ' ',     ' '),
    'oxygen_corr_100':       (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   'X',   ' ',  ' ',     ' '),
    'oxygen_corr_interval':  (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   'X',   ' ',  ' ',     ' '),
    'oxygen_regulation_P':   (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   'X',   ' ',  ' ',     ' '),
    'oxygen_regulation_D':   (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   'X',   ' ',  ' ',     ' '),
    'blower_off_time':       (' ',   'X',      'X',       ' ',          ' ',     'X',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'timer_heating_period':  ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   'X',  ' ',     ' '),
    'timer_hotwater_period': ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   'X',  ' ',     ' '),
    'timer_heating_start_1': ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   'X',  ' ',     ' '),
    'timer_heating_start_2': ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   'X',  ' ',     ' '),
    'timer_heating_start_3': ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   'X',  ' ',     ' '),
    'timer_heating_start_4': ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   'X',  ' ',     ' '),
    'timer_hotwater_start_1':('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   'X',  ' ',     ' '),
    'timer_hotwater_start_2':('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   'X',  ' ',     ' '),
    'timer_hotwater_start_3':('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   'X',  ' ',     ' '),
    'comp_clean_interval':   ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  'X',     ' '),
    'comp_clean_time':       ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  'X',     ' '),
    'comp_clean_blower':     (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  'X',     ' '),
    'comp_clean_wait':       (' ',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  'X',     ' '),
    'blower_corr_mid':       ('X',   'X',      'X',       ' ',          ' ',     'X',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'min_power':             ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'max_power':             ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'burner_off':            ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'burner_on':             ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'reset_alarm':           ('X',   'X',      'X',       ' ',          ' ',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
    'magazine_content':      ('X',   'X',      'X',       'X',          'X',     ' ',   ' ',     ' ',   ' ',   ' ',  ' ',     ' '),
}
