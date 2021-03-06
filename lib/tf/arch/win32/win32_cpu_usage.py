#
#  Copyright (C) 2009 TribleFlame Oy
#  
#  This file is part of TF.
#  
#  TF is free software: you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#  
#  TF is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#
# From http://code.activestate.com/recipes/576631/
# Copyright by author.
#
import ctypes
from ctypes import byref
from ctypes import Structure, Union
from ctypes.wintypes import *

__author__ = 'Shao-chuan Wang'

LONGLONG = ctypes.c_longlong
HQUERY = HCOUNTER = HANDLE
pdh = ctypes.windll.pdh
Error_Success = 0x00000000


class PDH_Counter_Union(Union):
    _fields_ = [('longValue', LONG),
                ('doubleValue', ctypes.c_double),
                ('largeValue', LONGLONG),
                ('AnsiStringValue', LPCSTR),
                ('WideStringValue', LPCWSTR)]


class PDH_FMT_COUNTERVALUE(Structure):
    _fields_ = [('CStatus', DWORD),
                ('union', PDH_Counter_Union)]

g_cpu_usage = 0


class QueryCPUUsage:

    def __init__(self):
        self.hQuery = HQUERY()
        self.hCounter = HCOUNTER()
        if not pdh.PdhOpenQueryW(None,
                                 0,
                                 byref(self.hQuery)) == Error_Success:
            raise Exception
        if not pdh.PdhAddCounterW(self.hQuery,
                                 u'''\\Processor(_Total)\\% Processor Time''',
                                 0,
                                 byref(self.hCounter)) == Error_Success:
            raise Exception

#    def run(self):
#        while True:
#            global g_cpu_usage
#            g_cpu_usage = self.getCPUUsage()
#            print 'cpu_usage: %d' % g_cpu_usage

    def getCPUUsage(self):
        PDH_FMT_LONG = 0x00000100
        if not pdh.PdhCollectQueryData(self.hQuery) == Error_Success:
            raise Exception
        ctypes.windll.kernel32.Sleep(1000)
        if not pdh.PdhCollectQueryData(self.hQuery) == Error_Success:
            raise Exception

        dwType = DWORD(0)
        value = PDH_FMT_COUNTERVALUE()
        if not pdh.PdhGetFormattedCounterValue(self.hCounter,
                                          PDH_FMT_LONG,
                                          byref(dwType),
                                          byref(value)) == Error_Success:
            raise Exception

        return value.union.longValue * 100
