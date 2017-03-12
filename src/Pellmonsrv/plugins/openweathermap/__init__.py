#! /usr/bin/python
# -*- coding: utf-8 -*-
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

from Pellmonsrv.plugin_categories import protocols
from Pellmonsrv.database import Getsetitem, Storeditem
from logging import getLogger
from threading import Timer
from time import sleep


logger = getLogger('pellMon')

class owmplugin(protocols):
    def __init__(self):
        protocols.__init__(self)

    def activate(self, conf, glob, db, *args, **kwargs):
        try:
            import pyowm
        except ImportError:
            logger.info('Python module pyowm is missing')
            raise
        protocols.activate(self, conf, glob, db, *args, **kwargs)
        self.itemrefs = []
        self.storeditems = {}
        self.itemvalues = {}

        try:
            self.owm = pyowm.OWM(self.conf['apikey'])
        except:
            logger.info('openweathermap init failed, invalid api_key')
            raise

        def additem(i, item_type='R'):
            i.tags = ['All', 'Basic', 'Openweathermap']
            i.type = item_type
            i.min = ''
            i.max = ''
            self.db.insert(i)
            self.itemrefs.append(i)

        def update_location(*args, **kwargs):
            self.update_interval = 1
            self.store_interval = 10

        config = {}
        for index_key, value in self.conf.items():
            if '_' in index_key:
                index, key = index_key.split('_')
                try:
                    config[index][key] = value
                except KeyError:
                    config[index] = {key:value}

        for index, itemconf in config.items():
            try:
                itemname = itemconf.pop('item')
                itemvalue = itemconf.pop('value', '0')
                itemdata = itemconf.pop('data');

                storeditem = Storeditem('owm_stored_'+itemdata, itemvalue)
                self.db.insert(storeditem)
                self.storeditems[itemdata] = storeditem
                self.itemvalues[itemdata] = storeditem.value

                i = Getsetitem(itemname, itemvalue, getter=lambda item, d=itemdata:self.itemvalues[d])

                for key, value in itemconf.items():
                    setattr(i, key, value)
                additem(i)

            except KeyError:
                pass

        i = Storeditem('location', 'copenhagen,dk', setter=update_location)
        i.description = 'Set your location: town,countrycode or zipcode,countrycode'
        additem(i, 'R/W')

        self.update_interval = 5

        t = Timer(0, self.update_thread)
        t.setDaemon(True)
        t.start()

    def update_thread(self):
        self.store_interval = 10
        while True:
            sleep(1)
            self.update_interval -= 1
            self.store_interval -=1
            if self.update_interval <= 0:
                try:
                    observation = self.owm.weather_at_place(self.db['location'].value.encode('utf-8'))
                    weather = observation.get_weather()
                    temperature = weather.get_temperature(self.conf['unit'])
                    wind = weather.get_wind()
                    humidity = weather.get_humidity()
                    self.itemvalues['wind_speed'] = unicode(wind['speed'])
                    self.itemvalues['wind_direction'] = unicode(wind['deg']) 
                    self.itemvalues['temperature'] = unicode(temperature['temp'])
                    self.itemvalues['humidity'] = unicode(humidity)
                    t = float(self.itemvalues['temperature'])
                    w = float(self.itemvalues['wind_speed'])
                    h = float(self.itemvalues['humidity'])
                    feelslike = t + 0.348*( 
                                            (h/100)*6.105*(2.7182**((17.27*t)/(237.7+t)) )
                                          ) - 0.7*w
                    self.itemvalues['feelslike'] = '%.1f'%feelslike
                except Exception as e:
                    logger.info('Openweathermap update error')
                    self.update_interval = 300
                else:
                    self.update_interval = 900
            if self.store_interval <= 0:
                for itemdata, storeditem in self.storeditems.items():
                    storeditem.value = self.itemvalues[itemdata]
                self.store_interval = 7200


