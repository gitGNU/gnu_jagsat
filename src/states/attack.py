#
#  Copyright (C) 2009 The JAGSAT project team.
#
#  This software is in development and the distribution terms have not
#  been decided yet. Therefore, its distribution outside the JAGSAT
#  project team or the Project Course evalautors in Abo Akademy is
#  completly forbidden without explicit permission of their authors.
#

from base.signal import weak_slot
from base.log import get_log
from game import GameSubstate
import random

from PySFML import sf
from tf.gfx import ui
import ui.widget
import ui.theme

_log = get_log (__name__)


class AttackState (GameSubstate):
    """
    TODO: Automatic pass to next phase when no more attacks are possible?
    """
    
    def do_setup (self, *a, **k):
        super (AttackState, self).do_setup (*a, **k)
        game = self.game

	game.world.phase = 'attack'

        if game.world.use_on_attack:
            game.ui_world.enable_used ()
        game.ui_world.enable_picking (
            lambda r:
            r.model.owner == game.world.current_player and
            r.model.can_attack,
            lambda p, r:
            r.model.owner != game.world.current_player and
            r.model.definition in p.model.definition.neighbours)
        game.ui_world.on_pick_regions += self._on_attack
        
        self.manager.enter_state (
            'message', message =
            "Attack phase for player %s.\n"
            "%%30%%You are ready to attack your enemies."
            % game.world.current_player.name,
            position = game.world.current_player.position)

    def do_release (self):
        if self.game.world.use_on_attack:
            self.game.world.clean_used ()
            self.game.ui_world.disable_used ()
	self.game.ui_world.disable_picking ()
        super (AttackState, self).do_release ()
    
    @weak_slot
    def _on_attack (self, src, dst):
        _log.debug ('Attacking from %s to %s.' %
                    (str (src.model), str (dst.model)))
        self.manager.enter_state ('risk_attack', attacker = src, defender = dst)
