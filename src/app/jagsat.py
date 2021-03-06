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

from functools import partial

from base.arg_parser import OptionWith, OptionFlag
from base.log import get_log
from base.conf import OptionConfFlag, GlobalConf
from core.app import GameApp

from tf.gfx import uihelp

from states.sandbox        import Sandbox
from states.root           import RootState
from states.root           import RootDialogState
from states.root           import RootYesNoDialogState
from states.root           import RootMessageState
from states.root           import RootInputDialogState
from states.game           import GameState
from states.init_game      import InitGameState
from states.ingame_menu    import IngameMenuState
from states.round          import GameRoundState
from states.menu           import MainMenuState
from states.reinforcements import ReinforcementState
from states.attack	   import AttackState
from states.move	   import MovementState
from states.risk_attack    import RiskAttackState

import os
import os.path

_log = get_log (__name__)

class JagsatApp (GameApp):

    NAME = 'jagsat'
    
    OPTIONS = GameApp.OPTIONS + \
"""
Game options:
  -m, --map <file>    Map file to load.
      --music-on      Enable music.
      --music-off     Disable music.
  -s, --state <state> Initial state.
      --ratio-hack    Enable hack for the Asus tablet.
"""
    
    AUTHOR = 'The JAGSAT development team.'
    COPYRIGHT = 'Copyright (C) 2009 The JAGSAT development team.'

    def __init__ (self, *a, **k):
        super (JagsatApp, self).__init__ (*a, **k)

        self._arg_map   = OptionWith (str)
        self._arg_state = OptionWith (str)
        self._arg_rhack = OptionFlag ()
        
        self.root_state = 'root'

    def get_save_folder (self):
        return self._save_folder

    def setup_folders (self):
        super (JagsatApp, self).setup_folders ()
        self._save_folder = os.path.join (self.get_config_folder (), 'save')
        if not os.path.isdir (self._save_folder):
            os.makedirs (self._save_folder)
    
    def do_prepare (self, args):
        super (JagsatApp, self).do_prepare (args)

        args.add ('m',  'map',        self._arg_map)
        args.add ('s',  'state',      self._arg_state)
        args.add (None, 'ratio-hack', self._arg_rhack)
        args.add (None, 'music-on', OptionConfFlag (
            GlobalConf ().child ('global-music'), True))
        args.add (None, 'music-off', OptionConfFlag (
            GlobalConf ().child ('global-music'), False))
        
        self.add_state ('sandbox',          Sandbox)
        self.add_state ('root',             RootState)
        self.add_state ('game',             GameState)
        self.add_state ('init_game',        InitGameState)
        self.add_state ('game_round',       GameRoundState)
        self.add_state ('ingame_menu',      IngameMenuState)
	self.add_state ('main_menu',        MainMenuState)
	self.add_state ('reinforce',        ReinforcementState)
	self.add_state ('attack',	    AttackState)
	self.add_state ('move',		    MovementState)
	self.add_state ('risk_attack',      RiskAttackState)
        self.add_state ('message',          RootMessageState)
        self.add_state ('dialog',           RootDialogState)
        self.add_state ('yes_no_dialog',    RootYesNoDialogState)
        self.add_state ('input_dialog',     RootInputDialogState)

        self.add_state ('test_reinforce', partial (GameState,
                                                   test_phase='reinforce'))
        self.add_state ('test_attack',    partial (GameState,
                                                   test_phase='attack'))
        self.add_state ('test_move',      partial (GameState,
                                                   test_phase='move'))
    
    def do_execute (self, freeargs):
        GlobalConf ().child ('global-music').default (True)
        if self._arg_state.value:
            self.root_state = self._arg_state.value

        if self._arg_rhack.value:
            uihelp.xratio = 1366./1024
            
        super (JagsatApp, self).do_execute (freeargs)
