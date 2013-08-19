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


dataDescriptions = {          #name, unit, description
    'magazine_content':      ('magazine content', 'kg', 'Calculated magazine content'),
    'power':                 ('power', '%',  'Modulated power level'),
    'power_kW':              ('power kW', 'kW',  'Calculated power level'),
    'boiler_temp':           ('boiler temp', '°',  'Measured Boiler temperature'),
    'chute_temp':            ('chute temp', '°',  'Measured chute temperature'),
    'smoke_temp':            ('smoke temp', '°',  'Measured exhaust smoke temperature'),
    'oxygen':                ('oxygen level', '%',  'Measured oxygen level'),
    'light':                 ('light level', 'lux',  'Light sensor level'),
    'feeder_time':           ('feeder run time ', 's',  'Total feeder running time'),
    'ignition_time':         ('total ignition time', 's',  'Total running time for igniter'),
    'alarm':                 ('alarm', '',  'Indicated alarm'),
    'oxygen_desired':        ('desired oxygen level', '%',  'Desired oxygen level according to modulated power level'),
    'mode':                  ('mode', '',  'Burner run mode'),
    'model':                 ('model', '',  ''),
    'motor_time':            ('motor time', 's',  ''),
    'el_time':               ('electricity time', 's',  ''),
    'motor_time_perm':       ('motor time perm', 's',  ''),
    'el_time_perm':          ('el time perm', 's',  ''),
    'ignition_count':        ('number of ignitions', 'times',  'Total number of burner cold-startups'),
    'boiler_return_temp':    ('boiler return temp', '°',  'Temperature of return flow to boiler'),
    'hotwater_temp':         ('hotwater temp', '°',  'Temperature in hotwater boiler'),
    'outside_temp':          ('outside temp', '°',  'Outside temperature'),
    'indoor_temp':           ('indoor temp', '°',  'Indoor temperature'),
    'flow':                  ('flow', 'l/s',  'Water flow'),
    'version':               ('version', '',  ''),
    'blower_low':            ('blower low', '%',  'Blower speed setting at 10% power'),
    'blower_high':           ('blower high', '%',  'Blower speed setting at 100% power'),
    'blower_mid':            ('blower mid', '%',  'Blower speed setting at 50% power'),
    'blower_cleaning':       ('blower cleaning', '%',  'Blower speed setting when cleaning grate'),
    'boiler_temp_set':       ('boiler desired temp', '°',  'Desired temperature for boiler water'),
    'boiler_temp_min':       ('boiler minimum temp', '°',  'Minimum temperature for boiler water'),
    'feeder_low':            ('feeder low', '',  ''),
    'feeder_high':           ('feeder high', '',  ''),
    'feed_per_minute':       ('feeds per minute', '/min',  ''),
    'boiler_temp_diff_up':   ('boiler temp upper diff', '°',  'Cut off temperature difference above desired temperature'),
    'boiler_temp_diff_down': ('boiler temp lower diff', '°',  'Cut off temperature difference below desired temperature'),
    'light_required':        ('required light level', 'lux',  'Required light sensor reading to stay in running mode'),
    'oxygen_regulation':     ('oxygen regulation', '',  'Oxygen regulation setting: OFF / Measure only / Regulate'),
    'oxygen_low':            ('oxygen level low ', '%',  'Required oxygen level at 10% power'),
    'oxygen_high':           ('oxygen level high', '%',  'Required oxygen level at 100% power'),
    'oxygen_mid':            ('oxygen level mid', '%',  'Required oxygen level at 50% power'),
    'oxygen_gain':           ('oxygen feeder gain', '',  'Pellet feeder capacity regulation by integrating difference between oxygen level and desired oxygen level'),
    'feeder_capacity_min':   ('feeder minimum capacity', 'g/360s',  'Minimum allowed feeder capacity'),
    'feeder_capacity':       ('feeder capacity', 'g/360s',  'Feeder capacity as set or altered by oxygen regulation'),
    'feeder_capacity_max':   ('feeder maximum capacity', 'g/360s',  'Maximum allowed feeder capacity'),
    'chimney_draught':       ('chimney draught', '',  'Higher setting increases pellet feeding at minimum power level'),
    'chute_temp_max':        ('maximum chute temperature', '°',  'Alarm level for chute temperature'),
    'regulator_P':           ('power regulator P', '',  'Proportional level for boiler temperature regulation'),
    'regulator_I':           ('power regulator I', '',  'Integral component for boiler temperature regulation'),
    'regulator_D':           ('power regulator D', '',  'Deriving component for boiler temperature regulation'),
    'blower_corr_low':       ('blower correction low', '%',  ''),
    'blower_corr_high':      ('blower correction high', '%',  ''),
    'cleaning_interval':     ('cleaning interval', 'min',  'Time interval at which blower speed is raised to clean the grate'),
    'cleaning_time':         ('cleaning time', 's',  'Time period with blower at cleaning speed setting when cleaning the grate'),
    'language':              ('language', '',  ''),
    'autocalculation':       ('autocalculation', '',  'When ON all feeder related settings are calculated from the feeder capacity setting'),
    'time_minutes':          ('minutes since midnight', 'min',  'Real time clock setting in minutes since midnight'),
    'oxygen_corr_10':        ('oxygen correction low', '%',  ''),
    'oxygen_corr_50':        ('oxygen correctin mid', '%',  ''),
    'oxygen_corr_100':       ('oxygen correction high', '%',  ''),
    'oxygen_corr_interval':  ('oxygen correctin interval', 's',  ''),
    'oxygen_regulation_P':   ('oxygen regulator P', '',  ''),
    'oxygen_regulation_D':   ('oxygen regulator D', '',  ''),
    'blower_off_time':       ('shutdown blower time', 'min',  ''),
    'timer_heating_period':  ('timer heating period', 'min',  'Number of minutes the burner should stay turned on when started by a timer in order to produce heat'),
    'timer_hotwater_period': ('timer hotwater period', 'min',  'Number of minutes the burner should stay turned on when started by a timer in order to produce hot water'),
    'timer_heating_start_1': ('timer heating start 1', 'min',  'Turn on the burner at n minutes since midnight'),
    'timer_heating_start_2': ('timer heating start 2', 'min',  'Turn on the burner at n minutes since midnight'),
    'timer_heating_start_3': ('timer heating start 3', 'min',  'Turn on the burner at n minutes since midnight'),
    'timer_heating_start_4': ('timer heating start 4', 'min',  'Turn on the burner at n minutes since midnight'),
    'timer_hotwater_start_1':('timer hotwater start 1', 'min',  'Turn on the burner at n minutes since midnight'),
    'timer_hotwater_start_2':('timer hotwater start 3', 'min',  'Turn on the burner at n minutes since midnight'),
    'timer_hotwater_start_3':('timer hotwater start 4', 'min',  'Turn on the burner at n minutes since midnight'),
    'comp_clean_interval':   ('compressor cleaning interval', 'kg',  'Compressor cleaning is started when this amount of pellet is burned'),
    'comp_clean_time':       ('compressor cleaning time', 's',  'Time period when the pressurized air valve is open'),
    'comp_clean_blower':     ('blower for compressor cleaning', '%',  'Blower speed setting for compressor cleaning'),
    'comp_clean_wait':       ('wait before compressor cleaning', 's',  'Time without feeding pellet before compressor cleaning is engaged'),
    'blower_corr_mid':       ('blower correction mid', '%',  ''),
    'min_power':             ('minimum power', '%',  'The power output is modulated down to this level, not below'),
    'max_power':             ('maximum power', '%',  'The power output is modulated up to this level, not above'),
    'burner_off':            ('burner OFF', '',  'Switch to off mode, if running the burner will go through the shutdown sequence'),
    'burner_on':             ('burner ON', '',  'Switch to run mode, the burner will start automatically when the temperature falls below set point'),
    'reset_alarm':           ('reset alarm', '',  'Reset alarm'),
}









