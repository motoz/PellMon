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
from cherrypy.lib.static import serve_file
from mako.template import Template
from mako.lookup import TemplateLookup
from time import time,localtime

lookup = TemplateLookup(directories=[os.path.join(os.path.dirname(__file__), 'html')])

class Consumption(object):    

    def __init__(self, polling, db):
        self.polling=polling
        self.db = db
        
    @cherrypy.expose
    def consumption(self):
        if not self.polling:
            return ""
        tmpl = lookup.get_template("consumption.html")
        return tmpl.render()
    
    @cherrypy.expose
    def consumption24h(self):    
        if not self.polling:
             return None
        graph_file = os.path.join(os.path.dirname(self.db), 'consumption24h.png')
        cherrypy.response.headers['Pragma'] = 'no-cache'
        now=int(time())/3600*3600
        
        RrdGraphString1="rrdtool graph "+graph_file+" --right-axis 1:0 --right-axis-format %%1.1lf --width 460 --height 300 --end %u --start %u-86400s "%(now,now)
        RrdGraphString1=RrdGraphString1+"DEF:a=%s:feeder_time:AVERAGE DEF:b=%s:feeder_capacity:AVERAGE "%(self.db,self.db)
        for h in range(0,24):
            start=(now-h*3600-3600)
            end=(now-h*3600)
            RrdGraphString1=RrdGraphString1+" CDEF:aa%u=TIME,%u,LE,TIME,%u,GT,a,0,IF,0,IF,b,*,360000,/ VDEF:va%u=aa%u,TOTAL CDEF:ca%u=a,POP,va%u CDEF:aaa%u=TIME,%u,LE,TIME,%u,GT,ca%u,0,IF,0,IF AREA:aaa%u%s"%(h,end,start,h,h,h,h,h,end,start,h,h,("#61c4f6","#4891b6")[h%2])

        RrdGraphString1=RrdGraphString1+" CDEF:cons=a,b,*,360,/,1000,/ VDEF:tot=cons,TOTAL CDEF:avg=a,POP,tot,24,/ VDEF:aver=avg,MAXIMUM GPRINT:tot:\"last 24h\: %.1lf kg\" GPRINT:aver:\"average %.2lf kg/h\" "
        RrdGraphString1=RrdGraphString1+" >>/dev/null"
        os.system(RrdGraphString1)        
        return serve_file(graph_file, content_type='image/png')

    @cherrypy.expose
    def consumption7d(self):    
        if not self.polling:
             return None
        graph_file = os.path.join(os.path.dirname(self.db), 'consumption7d.png')
        cherrypy.response.headers['Pragma'] = 'no-cache'
        t=time()
        now=int(time())/86400*86400-(localtime(t).tm_hour-int(t)%86400/3600)*3600
        
        RrdGraphString1="rrdtool graph "+graph_file+" --right-axis 1:0 --right-axis-format %%1.1lf --width 460 --height 300 --end %u --start %u-604800s "%(now,now)
        RrdGraphString1=RrdGraphString1+"DEF:a=%s:feeder_time:AVERAGE DEF:b=%s:feeder_capacity:AVERAGE "%(self.db,self.db)
        for h in range(0,7):
            start=(now-h*86400-86400)
            end=(now-h*86400)
            RrdGraphString1=RrdGraphString1+" CDEF:aa%u=TIME,%u,LE,TIME,%u,GT,a,0,IF,0,IF,b,*,360000,/ VDEF:va%u=aa%u,TOTAL CDEF:ca%u=a,POP,va%u CDEF:aaa%u=TIME,%u,LE,TIME,%u,GT,ca%u,0,IF,0,IF AREA:aaa%u%s"%(h,end,start,h,h,h,h,h,end,start,h,h,("#61c4f6","#4891b6")[h%2])

        RrdGraphString1=RrdGraphString1+" CDEF:cons=a,b,*,360,/,1000,/ VDEF:tot=cons,TOTAL CDEF:avg=a,POP,tot,7,/ VDEF:aver=avg,MAXIMUM GPRINT:tot:\"last week\: %.1lf kg\" GPRINT:aver:\"average %.2lf kg/day\" "
        RrdGraphString1=RrdGraphString1+" >>/dev/null"
        os.system(RrdGraphString1)        
        return serve_file(graph_file, content_type='image/png')

    @cherrypy.expose
    def consumption1m(self):    
        if not self.polling:
             return None
        graph_file = os.path.join(os.path.dirname(self.db), 'consumption1m.png')
        cherrypy.response.headers['Pragma'] = 'no-cache'
        t=time()
        now=int(time()+4*86400)/(86400*7)*(86400*7)-(localtime(t).tm_hour-int(t)%86400/3600)*3600 -4*86400
        
        RrdGraphString1="rrdtool graph "+graph_file+" --right-axis 1:0 --right-axis-format %%1.1lf --width 460 --height 300 --end %u --start %u-4838400s "%(now,now)
        RrdGraphString1=RrdGraphString1+"DEF:a=%s:feeder_time:AVERAGE DEF:b=%s:feeder_capacity:AVERAGE "%(self.db,self.db)
        for h in range(0,8):
            start=(now-h*(86400*7)-(86400*7))
            end=(now-h*(86400*7))
            RrdGraphString1=RrdGraphString1+" CDEF:aa%u=TIME,%u,LE,TIME,%u,GT,a,0,IF,0,IF,b,*,360000,/ VDEF:va%u=aa%u,TOTAL CDEF:ca%u=a,POP,va%u CDEF:aaa%u=TIME,%u,LE,TIME,%u,GT,ca%u,0,IF,0,IF AREA:aaa%u%s"%(h,end,start,h,h,h,h,h,end,start,h,h,("#61c4f6","#4891b6")[h%2])

        RrdGraphString1=RrdGraphString1+" CDEF:cons=a,b,*,360,/,1000,/ VDEF:tot=cons,TOTAL CDEF:avg=a,POP,tot,8,/ VDEF:aver=avg,MAXIMUM GPRINT:tot:\"last two month\: %.1lf kg\" GPRINT:aver:\"average %.2lf kg/week\" "
        RrdGraphString1=RrdGraphString1+" >>/dev/null"
        os.system(RrdGraphString1)        
        return serve_file(graph_file, content_type='image/png')
        
    @cherrypy.expose
    def consumption1y(self):    
        if not self.polling:
             return None
        graph_file = os.path.join(os.path.dirname(self.db), 'consumption1y.png')
        cherrypy.response.headers['Pragma'] = 'no-cache'
        cherrypy.response.headers['Pragma'] = 'no-cache'
        t=time()
        now=int(time())/int(31556952/12)*int(31556952/12)-(localtime(t).tm_hour-int(t)%86400/3600)*3600
        
        RrdGraphString1="rrdtool graph "+graph_file+" --right-axis 1:0 --right-axis-format %%1.1lf --width 460 --height 300 --end %u --start %u-31556952s "%(now,now)
        RrdGraphString1=RrdGraphString1+"DEF:a=%s:feeder_time:AVERAGE DEF:b=%s:feeder_capacity:AVERAGE "%(self.db,self.db)
        for h in range(0,12):
            start=(now-h*(86400*30)-(86400*30))
            end=(now-h*(86400*30))
            RrdGraphString1=RrdGraphString1+" CDEF:aa%u=TIME,%u,LE,TIME,%u,GT,a,0,IF,0,IF,b,*,360000,/ VDEF:va%u=aa%u,TOTAL CDEF:ca%u=a,POP,va%u CDEF:aaa%u=TIME,%u,LE,TIME,%u,GT,ca%u,0,IF,0,IF AREA:aaa%u%s"%(h,end,start,h,h,h,h,h,end,start,h,h,("#61c4f6","#4891b6")[h%2])

        RrdGraphString1=RrdGraphString1+" CDEF:cons=a,b,*,360,/,1000,/ VDEF:tot=cons,TOTAL CDEF:avg=a,POP,tot,12,/ VDEF:aver=avg,MAXIMUM GPRINT:tot:\"last year\: %.1lf kg\" GPRINT:aver:\"average %.2lf kg/month\" "
        RrdGraphString1=RrdGraphString1+" >>/dev/null"
        os.system(RrdGraphString1)        
        return serve_file(graph_file, content_type='image/png')
    

