#
#  Copyright (C) 2009, 2010 JAGSAT Development Team (see below)
#  
#  This file is part of JAGSAT.
#  
#  JAGSAT is free software: you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#  
#  JAGSAT is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  
#  JAGSAT Development Team is:
#    - Juan Pedro Bolivar Puente
#    - Alberto Villegas Erce
#    - Guillem Medina
#    - Sarah Lindstrom
#    - Aksel Junkkila
#    - Thomas Forss
#

from weakref import ref
from base.log import get_log
from base.xml_util import AutoContentHandler
from xml.sax import SAXException, make_parser
from error import ModelError
from geom import *
import os

_log = get_log (__name__)


class MapError (ModelError):
    pass

def load_map_meta (file_name):
    """
    TODO: Optimize.
    """
    return load_map (file_name).meta

def load_map (file_name):
    try:
        reader = MapContentHandler ()
        parser = make_parser ()
        parser.setContentHandler (reader)
        file = 'file:' + \
                      (os.getcwd () + '/' if file_name [0] != '/' else '') + \
                      file_name
	_log.debug ('Loading map: ' + file)
	parser.parse (file)
    except SAXException, e:
        raise MapError ('Map parsing error: ' + str (e))

    reader.map.file_name = file_name
    return reader.map


class MapContentHandler (AutoContentHandler):

    def __init__ (self, *a, **k):
        super (MapContentHandler, self).__init__ (*a, **k)
        self.map       = None
        self.continent = None
        self.region    = None
        self.link      = None
        self.link_type = None
        self.points    = None
        self.shape     = None
        self.xscale    = 1
        self.yscale    = 1
        self.xoffset   = 0
        self.yoffset   = 0
        
    def _new_map (self, attrs):
        self.map = MapDef (background = attrs ['bg'])
        self.xscale  = float (attrs.get ('xscale', 1))
        self.yscale  = float (attrs.get ('yscale', 1))
        self.xoffset = float (attrs.get ('xoffset', 0))
        self.yoffset = float (attrs.get ('yoffset', 0))
        self.map.zoom = float (attrs.get ('zoom', 1.))
        
    def _new_meta (self, attrs):
        self.map.meta = MetaDef ()

    def _new_thumbnail (self, attrs): pass
    def _chr_thumbnail (self, content):
        self.map.meta.thumbnail = content

    def _new_author (self, attrs): pass
    def _chr_author (self, content):
        self.map.meta.author = content

    def _new_description (self, attrs): pass
    def _chr_description (self, content):
        self.map.meta.description = content

    def _new_continent (self, attrs):
        assert self.continent is None
        self.continent = ContinentDef (
            attrs.get ('name', ''),
            int (attrs.get ('troops', '0')))
        
    def _end_continent (self):
        self.map.continents [self.continent.name] = self.continent
        self.continent = None

    def _new_region (self, attrs):
        assert self.continent
        assert self.region is None
        self.region = RegionDef (
            attrs.get ('name', ''))

    def _end_region (self):
        self.region.continent = self.continent
        self.continent.regions.append (self.region)
        self.map.regions [self.region.name] = self.region
        self.region = None

    def _new_circle (self, attrs):
        assert self.shape is None
        assert self.region
        self.shape  = Circle (radius = int (attrs.get ('radius', '0')))
        self.points = []

    def _end_circle (self):
        if len (self.points) > 0:
            self.shape.center = self.points [0]
        self.region.shape = self.shape
        self.shape = None
        self.points = None

    def _new_polygon (self, attrs):
        assert self.shape is None
        assert self.region
        self.shape = Polygon ()
        self.points = []

    def _end_polygon (self):
        self.region.shape = self.shape
        self.shape.points = self.points
        self.shape = None
        self.points = []
        
    def _new_point (self, attrs):
        assert self.shape
        self.points.append (Point (int (attrs.get ('x', '0')) *
                                   self.xscale + self.xoffset,
                                   int (attrs.get ('y', '0')) *
                                   self.yscale + self.yoffset))
    
    def _new_link (self, attrs):
        assert self.link is None
        self.link = []
        self.link_type = attrs.get ('type', 'line')

    def _end_link (self):
        getattr (self, '_do_link_' + self.link_type) ()
        self.link_type = None
        self.link = None

    def _new_node (self, attrs):
        try:
            self.link.append (self.map.regions [attrs ['name']])
        except Exception, e:
            _log.debug (str (e))
            raise MapError (str (e))
    
    def _do_link_line (self):
        if len (self.link) > 1:
            old = self.link [0]
            for new in self.link [1:]:
                old.link (new)
                old = new

    def _do_link_circle (self):
        self._do_link_line ()
        if len (self.link) > 2:
            self.link [0].link (self.link [-1])

    def _do_link_pairs (self):
        if len (self.link) % 2:
            self.link = self.link [:-1]
        for i, x in enumerate (self.link [::2]):
            x.link (self.link [2*i+1])

    def _do_link_clique (self):
        if (len (self.link) > 1):
            for i, x in enumerate (self.link):
                for y in self.link [i:]:
                    if x != y:
                        x.link (y)
                    

class MetaDef (object):

    def __init__ (self,
                  thumbnail   = '',
                  author      = '',
                  description = '',
                  *a, **k):
        super (MetaDef, self).__init__ (*a, **k)

        self.thumbnail   = thumbnail
        self.author      = author
        self.description = description


class MapDef (object):

    def __init__ (self,
                  regions = None,
                  background = '',
                  meta = None,
                  *a, **k):
        super (MapDef, self).__init__ (*a, **k)
        if regions is None:
            regions = []

        self.regions    = dict ((r.name, r) for r in regions)
        self.continents = \
            dict ((r.continent.name, r.continent) for r in regions)

        self.meta = meta
        self.background = background


class RegionDef (object):

    def __init__ (self,
                  name = '',
                  continent = None,
                  neighbours = None,
                  shape = None,
                  *a, **k):
        
        super (RegionDef, self).__init__ (*a, **k)
        self.name       = name
        self.continent  = continent
        self.neighbours = [] if neighbours is None else neighbours
        self.shape      = shape
    
    def link (self, r):
        self.neighbours.append (r)
        r.neighbours.append (self)


class ContinentDef (object):

    def __init__ (self,
                  name = '',
                  troops = 0,
                  regions = None,
                  *a, **k):
        super (ContinentDef, self).__init__ (*a, **k)
        if regions is None:
            regions = []

        self.regions = regions
        self.troops  = troops
        self.name    = name
