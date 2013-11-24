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

from protocol import Frame

# 'FrameXXX' defines the serial bus response frame format
# [list of character count per value], 'string with the frame address'
FrameZ00  = Frame([5,5,5,5,5,5,5,10,10,5,5,5,5,5,5,5,5,5],'Z000000')
FrameZ01  = Frame([5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5], 'Z010000')
FrameZ02  = Frame([10,10,10,10],'Z020000')
FrameZ03  = Frame([5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5],'Z030000')
FrameZ04  = Frame([5,5],'Z040000')
FrameZ05  = Frame([5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5],'Z050000')
FrameZ06  = Frame([5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5],'Z060000')
FrameZ07  = Frame([5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5],'Z070000')    
FrameZ08  = Frame([5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5],'Z080000')    
