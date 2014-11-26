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
import os.path
import cherrypy
from cherrypy.lib.static import serve_file, serve_fileobj
from mako.template import Template
from mako.lookup import TemplateLookup
import time
from tempfile import NamedTemporaryFile
import subprocess
from math import isnan
import json
lookup = TemplateLookup(directories=[os.path.join(os.path.dirname(__file__), 'html')])


def make_barchart_string(db, end, align, div, bars, out='-', width=440, tot_txt='total', avg_unit='', tot_unit='kg', param=''):
    #Build the command string to make a graph from the database
    now = int(end)
    div = int(div)
    now1h=int(align)

    # The width passed to rrdtool does not include the sidebars
    graphWidth = str(int(width))

    consumption_file = out # Output to file 'out'

    # Draw one bar:
    # CDEF:rate=            # compute feeder_time rate * feeder_consumption for selected timespan
    # TIME,endtime, LE,     # push 1 if TIME is before endtime else push 0
    # TIME,starttime, GT,   # push 1 if TIME is after starttime else push 0
    # feeder_time,0, IF,    # push 0 before starttime, push from DEF:feeder_time after starttime
    # 0, IF,                # push back above result before endtime, then push 0 
                            # the stack now has feeder_time (rate) between starttime and endtime, otherwise zero
    # feeder_capacity, *,   # Multiply with DEF:feeder_capacity (which is for 360 seconds, and in grams)
    # 360000, /             # and divide by 360 to get capacity per second, and also by 1000 to get result in kg
    
    # VDEF:tot=rate,TOTAL   # tot = integration of the CDEF:rate, ie. get value for consumption between start and endtimes
    
    # CDEF:total=           # make a CDEF out of the VDEF:tot value by 'tricking' rrd;
    # feeder_time,POP,tot   # push from any DEF, pop the values, then push new values from the VDEF
    
    # CDEF:barchart=        # and finally...
    # TIME,endtime,LE,      # where time is between endtime
    # TIME,starttime,GT,    # and starttime
    # total,0,IF,           # push calculated total 
    # 0,IF                  # else push zero
    # AREA:barchart#ffffff" # draw an area below it      
    # Repeat for every bar            

    RrdGraphString1="rrdtool graph "+consumption_file+" --border 0 --disable-rrdtool-tag --full-size-mode --width "+graphWidth+" %s --right-axis-format %%1.1lf --height 400 --end %u --start %u-%us "%(param,now,now,div*bars)
    RrdGraphString1=RrdGraphString1+"DEF:a=%s:feeder_time:AVERAGE:end=%u:start=%u DEF:b=%s:feeder_capacity:AVERAGE:end=%u:start=%u DEF:b1h=%s:feeder_capacity:AVERAGE"%(db,now,now1h-div*bars,db,now,now1h-div*bars,db)

    h=bars+3
    start=(now1h-(bars-1)*div-div)
    end=(now1h-(bars-1)*div)
    part = 1
    RrdGraphString1=RrdGraphString1+" CDEF:aa%u=TIME,%u,LE,TIME,%u,GT,a,0,IF,0,IF,b,*,360000,/ VDEF:va%u=aa%u,TOTAL CDEF:ca%u=a,POP,va%u CDEF:aaa%u=TIME,%u,LE,TIME,%u,GT,ca%u,0,IF,0,IF,%f,* AREA:aaa%u%s"%(h,end,start,h,h,h,h,h,end,start,h,part,h,"#d6e4e9")
    h=bars-1
    part = 1
    start=(now-(bars-1)*div-div)
    RrdGraphString1=RrdGraphString1+" CDEF:aa%u=TIME,%u,LE,TIME,%u,GT,a,0,IF,0,IF,b,*,360000,/ VDEF:va%u=aa%u,TOTAL CDEF:ca%u=a,POP,va%u CDEF:aaa%u=TIME,%u,LE,TIME,%u,GT,ca%u,0,IF,0,IF,%f,* AREA:aaa%u%s"%(h,end,start,h,h,h,h,h,end,start,h,part,h,("#61c4f6","#4891b6")[h%2])

    for h in range(0,bars-1):
        start=(now1h-h*div-div)
        end=(now1h-h*div)
        RrdGraphString1=RrdGraphString1+" CDEF:aa%u=TIME,%u,LE,TIME,%u,GT,a,0,IF,0,IF,b,*,360000,/ VDEF:va%u=aa%u,TOTAL CDEF:ca%u=a,POP,va%u CDEF:aaa%u=TIME,%u,LE,TIME,%u,GT,ca%u,0,IF,0,IF AREA:aaa%u%s"%(h,end,start,h,h,h,h,h,end,start,h,h,("#61c4f6","#4891b6")[h%2])

    h=bars+1
    start=now1h
    end=now
    if now-now1h > 120:
        part=div/(float(now)-now1h-40)
        RrdGraphString1=RrdGraphString1+" CDEF:aa%u=TIME,%u,LE,TIME,%u,GT,a,0,IF,0,IF,b,*,360000,/ VDEF:va%u=aa%u,TOTAL CDEF:ca%u=a,POP,va%u CDEF:aaa%u=TIME,%u,LE,TIME,%u,GT,ca%u,0,IF,0,IF,%f,* AREA:aaa%u%s"%(h,end,start,h,h,h,h,h,end,start,h,part,h,"#d6e4e9")
        h=bars+2
        RrdGraphString1=RrdGraphString1+" CDEF:aa%u=TIME,%u,LE,TIME,%u,GT,a,0,IF,0,IF,b,*,360000,/ VDEF:va%u=aa%u,TOTAL CDEF:ca%u=a,POP,va%u CDEF:aaa%u=TIME,%u,LE,TIME,%u,GT,ca%u,0,IF,0,IF AREA:aaa%u%s"%(h,end,start,h,h,h,h,h,end,start,h,h,"#4891b6")

    RrdGraphString1=RrdGraphString1+" CDEF:cons=a,b1h,*,360,/,1000,/ VDEF:tot=cons,TOTAL CDEF:avg=b1h,POP,tot,%u,/ VDEF:aver=avg,MAXIMUM GPRINT:tot:\"%s %%.1lf %s\" GPRINT:aver:\"average %%.2lf %s\" "%(bars, tot_txt, tot_unit, avg_unit)
    return RrdGraphString1


class Consumption(object):    

    def __init__(self, polling, db):
        self.polling=polling
        self.db = db
        self.totals={}
        
    @cherrypy.expose
    def consumption(self):
        if not self.polling:
            return ""
        tmpl = lookup.get_template("consumption.html")
        return tmpl.render(username=cherrypy.session.get('_cp_username'), webroot=cherrypy.request.script_name)
    
    @cherrypy.expose
    def consumption24h(self):
        if not self.polling:
             return None
        now=int(time.time())
        align=now/3600*3600
        RrdGraphString = make_barchart_string(self.db, now, align, 3600, 24, '-', 550, '24h consumption', 'kg/h')
        cmd = subprocess.Popen(RrdGraphString +"--height 320", shell=True, stdout=subprocess.PIPE)
        cherrypy.response.headers['Pragma'] = 'no-cache'
        cherrypy.response.headers['Content-Type'] = "image/png"
        return cmd.communicate()[0]

    @cherrypy.expose
    def flotconsumption24h(self):
        if not self.polling:
             return None
        now=int(time.time())
        align=now/3600*3600
        jsondata = self.barchartdata(start=align, period=3600, bars=24)
        cherrypy.response.headers['Pragma'] = 'no-cache'
        return jsondata

    @cherrypy.expose
    def consumption7d(self):
        if not self.polling:
             return None
        now=int(time.time())
        align=int(now)/86400*86400-(time.localtime(now).tm_hour-int(now)%86400/3600)*3600
        RrdGraphString = make_barchart_string(self.db, now, align, 86400, 7, '-', 550, 'last week', 'kg/day')
        cmd = subprocess.Popen(RrdGraphString +"--height 320", shell=True, stdout=subprocess.PIPE)
        cherrypy.response.headers['Pragma'] = 'no-cache'
        cherrypy.response.headers['Content-Type'] = "image/png"
        return cmd.communicate()[0]

    @cherrypy.expose
    def flotconsumption7d(self):
        if not self.polling:
             return None
        now=int(time.time())
        align=int(now)/86400*86400-(time.localtime(now).tm_hour-int(now)%86400/3600)*3600
        jsondata = self.barchartdata(start=align, period=3600*24, bars=7)
        cherrypy.response.headers['Pragma'] = 'no-cache'
        return jsondata

    @cherrypy.expose
    def consumption1m(self):    
        if not self.polling:
             return None
        now = int(time.time())
        align=int(now+4*86400)/(86400*7)*(86400*7)-(time.localtime(now).tm_hour-int(now)%86400/3600)*3600 -4*86400
        RrdGraphString = make_barchart_string(self.db, time.time(), align, 86400*7, 8, '-', 550, 'last two months', 'kg/week')
        cmd = subprocess.Popen(RrdGraphString +"--height 320", shell=True, stdout=subprocess.PIPE)
        cherrypy.response.headers['Pragma'] = 'no-cache'
        cherrypy.response.headers['Content-Type'] = "image/png"
        return cmd.communicate()[0]

    @cherrypy.expose
    def flotconsumption1m(self):
        if not self.polling:
             return None
        now = int(time.time())
        align=int(now+4*86400)/(86400*7)*(86400*7)-(time.localtime(now).tm_hour-int(now)%86400/3600)*3600 -4*86400
        jsondata = self.barchartdata(start=align, period=3600*24*7, bars=8)
        cherrypy.response.headers['Pragma'] = 'no-cache'
        return jsondata

    @cherrypy.expose
    def consumption1y(self):    
        if not self.polling:
             return None
        now = int(time.time())
        align=now/int(31556952/12)*int(31556952/12)-(time.localtime(now).tm_hour-int(now)%86400/3600)*3600
        RrdGraphString = make_barchart_string(self.db, now, align, 2628000, 12, '-', 550, 'last year', 'kg/month')
        cmd = subprocess.Popen(RrdGraphString +"--height 320", shell=True, stdout=subprocess.PIPE)
        cherrypy.response.headers['Pragma'] = 'no-cache'
        cherrypy.response.headers['Content-Type'] = "image/png"
        return cmd.communicate()[0]

    @cherrypy.expose
    def flotconsumption1y(self):    
        if not self.polling:
             return None
        now = int(time.time())
        align1y=now/int(31556952/12)*int(31556952/12)-(time.localtime(now).tm_hour-int(now)%86400/3600)*3600
        jsondata = self.barchartdata(start=align1y, period=3600*24*30, bars=12)
        cherrypy.response.headers['Pragma'] = 'no-cache'
        return jsondata

    def barchartdata(self, start=0, period=3600, bars=1):
        is_dst = time.daylight and time.localtime().tm_isdst > 0
        utc_offset = - (time.altzone if is_dst else time.timezone)
        try:
            period = int(period)
            start = int(start)
            bars = int(bars)
            now = int(time.time())
            if start==0:
                start = now
            bardata=[]
            total=0
            for i in range(bars)[::-1]:
                to_time = start - period*i
                from_time = to_time - period 
                try:
                    bar = float(self.rrd_total(from_time, to_time)[1:][:-1])
                    if isnan(bar):
                        bar = 0
                except Exception,e:
                    print str(e)
                    bar=0
                bardata.append([(from_time + utc_offset)*1000, bar])
                total += bar
            lastbar = float(self.rrd_total(start, now, cache=False)[1:][:-1])
            if isnan(lastbar):
                lastbar = 0
            if now-start > 100:
                predictedbar = (float(period) / (now-start)) * lastbar
            else:
                predictedbar = 0
            bardata_ = []
            bardata_.append( { 'bars':{'barWidth':(now-start)*1000}, 'color':"#cdcdcd", 'data':[[(start+utc_offset)*1000, predictedbar]]} )
            bardata_.append( { 'bars':{'barWidth':(now-start)*1000}, 'data':[[(start+utc_offset)*1000, lastbar]]} )
            bardata_.append( {'data':bardata} ) 
            average = total / bars
            return json.dumps({'bardata':bardata_, 'total':total, 'average':average})
        except Exception, e:
            return None

    def rrd_total(self, start, end, cache=True):
        start = str(start)
        end = str(end)
        try:
            total = self.totals[start][end]
        except:
            command = ['rrdtool', 'graph', '--start', start, '--end', end,'-', 'DEF:a=%s:feeder_time:AVERAGE'%self.db,'DEF:b=%s:feeder_capacity:AVERAGE'%self.db, 'CDEF:c=a,b,*,360000,/', 'VDEF:s=c,TOTAL', 'PRINT:s:\"%.2lf\"']
            cmd = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
            try:
                total = cmd.communicate()[0].splitlines()[1]
            except:
                total = None
            if total and cache:
                if not start in self.totals:
                    self.totals[start] = {}
                self.totals[start][end] = total
        return total
