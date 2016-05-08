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

import os
from langmap import langmap
try:
    from directories import DATADIR
    langfile = os.path.join(DATADIR, 'Pellmonsrv', 'plugins', 'nbecom', 'lang.uk.prop')
except ImportError:
    langfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'language', 'lang.uk.prop')


lang = [map(lambda l:l.rstrip(), l.split('=')) for l in open(langfile)]
lang_value_to_text = dict(lang)

def get_settings_enumerations(langtext):
    value_to_text = {k.split(langtext)[1]:v for k, v in lang if k.startswith(langtext)}
    text_to_value = {v:k for k, v in value_to_text.items()}
    return (value_to_text, text_to_value)

enumdicts = {}

enumdict_outputs =  get_settings_enumerations('lng_grid_output_')

enumdicts['cleaning-output_ash'] = enumdict_outputs
enumdicts['cleaning-output_boiler1'] = enumdict_outputs
enumdicts['cleaning-output_boiler2'] = enumdict_outputs
enumdicts['cleaning-output_burner'] = enumdict_outputs
enumdicts['fan-output_exhaust'] = enumdict_outputs
enumdicts['hot_water-output'] = enumdict_outputs
enumdicts['pump-output'] = enumdict_outputs
enumdicts['sun-output_excess'] = enumdict_outputs
enumdicts['sun-output_pump'] = enumdict_outputs
enumdicts['weather-output_pump'] = enumdict_outputs
enumdicts['weather2-output_pump'] = enumdict_outputs
enumdicts['weather-output_up'] = enumdict_outputs
enumdicts['weather2-output_up'] = enumdict_outputs
enumdicts['weather-output_down'] = enumdict_outputs
enumdicts['weather2-output_down'] = enumdict_outputs

enumdicts['oxygen-lambda_type'] =  get_settings_enumerations('lng_settings_fieldtype_lambdatype_')
enumdicts['oxygen-regulation'] =  get_settings_enumerations('lng_settings_fieldtype_regulation_')

on_off_alarm = {'0':'Off', '1':'On', '2':'Alarm', '3':'Unresettable alarm'}
on_off_alarm_reverse = {v:k for k,v in on_off_alarm.items()}
enumdicts['operating_data-off_on_alarm'] = (on_off_alarm, on_off_alarm_reverse)




def event_text(code):
    try:
        return lang_value_to_text[lang_value_to_text['setup_%s'%code]]
    except KeyError:
        return code

def state_text(code):
    try:
        return lang_value_to_text['state_%s'%code]
    except KeyError:
        return code

def substate_text(code):
    try:
        return lang_value_to_text['lng_substate_%s'%code]
    except KeyError:
        return code

def get_enumeration_function(name):
    v2t, t2v = enumdicts[name]
    return lambda name, reverse=False:v2t[name] if not reverse else t2v[name]

def get_enumeration_list(name):
    return sorted(enumdicts[name][0].items(), key=lambda x:int(x[0]))

def lang_longname(i_id):
    return lang_value_to_text[langmap[i_id]]

def lang_description(i_id):
    return lang_value_to_text[langmap[i_id]+'_TP']

