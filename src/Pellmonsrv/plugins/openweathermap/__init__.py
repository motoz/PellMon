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

        i = Storeditem('location', 'copenhagen,dk', setter=update_location)
        i.description = 'Set your location: town,countrycode or zipcode,countrycode'
        additem(i, 'R/W')

        i = Getsetitem('outside_temp', '-', getter=lambda item:self.temperature)
        i.description = 'Current temperature at your location from openweathermap.com'
        additem(i)

        self.storedtemp = Storeditem('owm_storedtemperature', '0')
        self.db.insert(self.storedtemp)
        self.temperature = self.storedtemp.value
        self.update_interval = 5

        t = Timer(0, self.update_thread)
        t.setDaemon(True)
        t.start()

    def getMenutags(self):
        return ['Openweathermap']

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
                    self.temperature = unicode(temperature['temp'])
                except Exception as e:
                    logger.info('Openweathermap update error')
                    self.update_interval = 300
                else:
                    self.update_interval = 1800
            if self.store_interval <= 0:
                self.storedtemp.value = self.temperature
                self.store_interval = 7200


