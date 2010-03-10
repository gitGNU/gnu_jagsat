#
#  Copyright (C) 2009 The JAGSAT project team.
#
#  This software is in development and the distribution terms have not
#  been decided yet. Therefore, its distribution outside the JAGSAT
#  project team or the Project Course evalautors in Abo Akademy is
#  completly forbidden without explicit permission of their authors.
#

from base.log import get_log
from base import signal
from player import move_to_player_position

from tf.gfx import ui
import widget
import theme
import random

from PySFML import sf

_log = get_log (__name__)

class AttackComponent (ui.FreeformContainer, object):

    def __init__ (self,
                  parent = None,
                  attacker = None,
                  defender = None,
                  *a, **k):
        super (AttackComponent, self).__init__ (parent, *a, **k)
        self.width = 1024
        self.height = 768
        
	self._dice_enabled = False
        self._sprite = None
        
        self.attacker = attacker
        self.defender = defender
        
	self.defender_dice_list = []
	self.attacker_dice_list = []

	self.attacker_number_of_dices = 1
	self.defender_number_of_dices = 1
        
        self._box_attacker = widget.VBox (parent)
        self._box_attacker_a = widget.HBox (self._box_attacker)
        self._box_attacker_b = widget.HBox (self._box_attacker)
        self._box_attacker.padding_bottom = 10
        self._box_attacker_a.padding_left = 10
        self._box_attacker_b.padding_left = 10
        
        self._box_defender = widget.VBox (parent)
        self._box_defender_a = widget.HBox (self._box_defender)
        self._box_defender_b = widget.HBox (self._box_defender)
        self._box_defender.padding_bottom = 10
        self._box_defender_a.padding_left = 10
        self._box_defender_b.padding_left = 10
        self._box_defender_b.set_center_rel (-0.5, 0)
        self._box_defender_b.set_position_rel (0.5, 0)
        
        move_to_player_position (self._box_attacker, self.attacker.owner)
        move_to_player_position (self._box_defender, self.defender.owner)
        
        self._attack_troops_increase = widget.SmallButton (
            self._box_attacker_a, None, 'data/icon/attacker-more.png')	
        self._attack_troops_decrease = widget.SmallButton (
            self._box_attacker_a, None, 'data/icon/attacker-less.png')
        self._but_attack_attack  = widget.SmallButton (
            self._box_attacker_b, None, 'data/icon/attack.png')
        self._but_attack_retreat = widget.SmallButton (
            self._box_attacker_b, None, 'data/icon/retreat.png')
        
	self._defense_troops_increase = widget.SmallButton (
            self._box_defender_a, None, 'data/icon/defender-more.png')
	self._defense_troops_decrease = widget.SmallButton (
            self._box_defender_a, None, 'data/icon/defender-less.png')
        self._but_defense_attack  = widget.SmallButton (
            self._box_defender_b, None, 'data/icon/attack.png')

        self._attack_troops_increase.on_click += \
            self.attacker_troops_increase
        self._attack_troops_decrease.on_click += \
            self.attacker_troops_decrease
        self._defense_troops_decrease.on_click += \
            self.defender_troops_decrease
        self._defense_troops_increase.on_click += \
            self.defender_troops_increase
	
        
    @signal.weak_slot
    def attacker_troops_increase(self, _):
	if self.attacker_number_of_dices < 3 and \
               self.attacker.troops > self.attacker_number_of_dices + 1:
	    self.attacker_number_of_dices += 1

    @signal.weak_slot
    def attacker_troops_decrease(self, _):
	if self.attacker_number_of_dices > 1:
	    self.attacker_number_of_dices -= 1

    @signal.weak_slot
    def defender_troops_increase(self, _):
	if self.defender_number_of_dices < 2 and \
               self.defender.troops > self.defender_number_of_dices:
	    self.defender_number_of_dices += 1

    @signal.weak_slot
    def defender_troops_decrease(self, _):
	if self.defender_number_of_dices > 1:
	    self.defender_number_of_dices -= 1
    
    def get_dice_enabled (self):
        return self._dice_enabled

    def set_dice_enabled (self, val):
        self._dice_enabled = val
        self._attack_troops_increase.set_visible (self._dice_enabled)
	self._attack_troops_decrease.set_visible (self._dice_enabled)
	self._defense_troops_increase.set_visible (self._dice_enabled)
	self._defense_troops_decrease.set_visible (self._dice_enabled)

    dice_enabled = property (get_dice_enabled, set_dice_enabled)
