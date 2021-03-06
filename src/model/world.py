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

from base.changer import InstChanger
from base.observer import make_observer
from map import load_map
from operator import attrgetter
from collections import defaultdict

def create_game (cfg):
    """
    Creates a game from a ConfNode containing the following childs:
      - player-X: with X \in [0, 5], contains the properties for
        player number X. See create_player.
      - map: Contains the path to the map file.
    """
    
    players = []
    for i in range (0, 6):
        pcfg = cfg.child ('player-' + str (i))
        if pcfg.child ('enabled').value:
            players.append (create_player (pcfg))

    map_ = load_map (cfg.child ('map').value)
    
    world = World (map_, players)
    world.use_on_attack = cfg.child ('use-on-attack').value
    world.use_on_move   = cfg.child ('use-on-move').value
    world.name          = cfg.name
    
    return world

def create_player (cfg):
    """
    Creates a player from a ConfNode containing the following childs:
      - color: The color of the player.
      - position: The position of the player.
    """
    return Player (cfg.child ('name').value,
                   cfg.child ('color').value,
                   cfg.child ('position').value)

WorldSubject, WorldListener = \
    make_observer (['on_set_world_current_player',
                    'on_set_world_phase',
                    'on_set_world_round'],
                   'World', __name__)

class World (WorldSubject):

    phase          = InstChanger ('on_set_world_phase', 'phase', 'init')
    round          = InstChanger ('on_set_world_round', 'round', 0)
    current_player = InstChanger ('on_set_world_current_player',
                                  'current_player', None)

    def __init__ (self, map_ = None, players = None, name = 'default', *a, **k):
        assert map_
        super (World, self).__init__ (*a, **k)

        self.use_on_move    = True
        self.use_on_attack  = True
        self.map            = map_
        self.name           = name
        self.current_player = None
        self.first_player   = None
        self._players = {} if players is None \
                           else dict ((p.name, p) for p in players)
        self._regions = dict ((r.name, Region (r))
                              for r in map_.regions.itervalues ())

    def clean_used (self):
        for r in self._regions.itervalues ():
            r.troops += r.used
            r.used = 0
    
    @property
    def regions (self):
        return self._regions

    def regions_of (self, player):
        return filter (lambda r: r.owner == player, self._regions.itervalues ())

    @property
    def players (self):
        return self._players

    def ordered_players (self):
        players = self._players.values ()
        players.sort (key = attrgetter ('position'))
        return players

    def check_alive (self, player):
        return bool (self.regions_of (player))
                
    def find_components (self, criteria = lambda x: True):
        table = defaultdict (set)
        for r in self.regions.itervalues ():
            if criteria (r):
                self.find_component (r, table, set (), criteria)
        return table

    def find_component (self,
                        region,
                        table,
                        component,
                        criteria = lambda x: True):
        if table [region]:
            return
        table [region] = component
        component.add (region)
        for r in region.definition.neighbours:
            r = self.regions [r.name]
            if criteria (r):
                self.find_component (r, table, component, criteria)

RegionSubject, RegionListener = \
    make_observer (['on_set_region_troops',
                    'on_set_region_used',
                    'on_set_region_owner'],
                   'Region', __name__)

class Region (RegionSubject):
    
    troops = InstChanger ('on_set_region_troops', 'troops', 0)
    used   = InstChanger ('on_set_region_used',   'used', 0)
    owner  = InstChanger ('on_set_region_owner',  'owner', None)
    
    def __init__ (self, definition = None, *a, **k):
        assert definition
        super (Region, self).__init__ (*a, **k)
        
        self.definition = definition
                
    @property
    def total (self):
        return self.troops + self.used

    @property
    def can_attack (self):
        return self.total > 1 and self.troops > 0

class card:
    infantry, cavalry, artillery, wildcard = range (4)

class position:
    n, ne, se, s, sw, nw = range (6)


def cardset_value (cards):
    ncard = defaultdict (lambda: 0)
    total = 0 
    for x in cards:
        ncard [x] += 1
        total     += 1
    
    if total != 3:
        return 0
    if ncard [card.infantry]  + ncard [card.wildcard] == 3:
        return 3
    if ncard [card.cavalry]   + ncard [card.wildcard] == 3:
        return 5
    if ncard [card.artillery] + ncard [card.wildcard] == 3:
        return 8
    if ncard [card.artillery] != 2 and ncard [card.cavalry] != 2 and \
       ncard [card.artillery] != 2:
        return 10
    return 0


PlayerSubject, PlayerListener = \
    make_observer (['on_set_player_troops',
                    'on_set_player_alive',
                    'on_add_player_card',
                    'on_del_player_card' ])

class Player (PlayerSubject):

    troops = InstChanger ('on_set_player_troops', 'troops', 0)
    alive  = InstChanger ('on_set_player_alive',  'alive',  True)
    
    def __init__ (self,
                  name = 'Unnamed',
                  color = None,
                  position = position.n,
                  mission  = None,
                  *a, **k):
        super (Player, self).__init__ (*a, **k)
                
        self.name       = name
        self.color      = color
        self.position   = position
        self.mission    = None
        self._cards     = []
        self.conquered  = 0
        
    @property
    def cards (self):
        return tuple (self._cards)

    def add_card (self, card):
        self._cards.append (card)
        self.on_add_player_card (self, card)

    def del_card (self, card):
        self._cards.remove (card)
        self.on_del_player_card (self, card)

