#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import namedtuple, defaultdict
import numpy as np
from functools import partial
from scipy.stats import vonmises_line
from numbers import Number
import context as con
from scipy.stats import truncnorm

choice = np.random.choice


# import categories as cat
# from outcomes import Tree
# import tensorflow as tf


SCALE = 10
attribute_default = 1
# attribute_max = (20 * SCALE) + ATTRIBUTE_DEFAULT_VALUE

Positions = ['DH', 'P', 'C', '1B','2B', '3B','SS',
             'LF', 'CF','RF', 'Bench', 'Unavailable']

AttributeBundle = namedtuple('AttributeBundle',
                             ['strength', 'movement', 'fatigue'])

QualityBundle = namedtuple('QualityBundle',
                           ['accuracy', 'precision', 'flexibility'])


def pos_from_str(pos_name):
    assert pos_name in Positions
    return Positions.index(pos_name)

    
    
class BasePlayer(object):
    def __init__(self, num=0, pos=pos_from_str('Bench'), team=None):
        super().__init__()
        self._num = num
        self._pos = pos
        self._team = team
        
    @property
    def team(self):
        return self._team

    @property
    def num(self):
        return self._num

    @property
    def pos(self):
        return self._pos
        
    @property
    def posname(self):
        return Positions[self.pos]
        
    @pos.setter
    def pos(self, pos_name):
        assert isinstance(pos_name, str)
        assert pos_name in Positions
        self._pos = pos_from_str(pos_name)
    
    def __repr__(self):
        return str('Player(' \
                + str(self.num) + ',' \
                + Positions[self.pos] + ',' \
                + str(self.team) + ')')
    
class Player(BasePlayer):            
    def __init__(self, num, pos_name, team):
        assert isinstance(num, Number)
        assert isinstance(pos_name, str)
        assert isinstance(team, str)
        super().__init__(num, pos_from_str(pos_name), team)

    @property
    def error_check(self):
        raise NotImplementedError
        
    @property
    def injury_check(self):
        raise NotImplementedError 
    
    def make_decision(self, action_type_name, *args):
        return NotImplementedError
        
class BayesPlayer(Player):
    def __init__(self, num, pos, team, stren, move, fatig):
        super().__init__(num, pos, team)
        self._learnability = NotImplemented
        self._risk = NotImplemented
        self.qualities = defaultdict(QualityBundle)
        self.attributes = AttributeBundle(
            strength=stren, movement=move, fatigue=fatig
        )
        
    @property
    def stren(self):
        return self.attributes.strength

    @property
    def move(self):
        return self.attributes.movement

    @property
    def fatig(self):
        return self.attributes.fatigue

    @property
    def quality(self, name):
        try:
            qual = self.qualities.get(name, attribute_default)
        except:
            raise ValueError('No player quality {}'.format(name))
        finally:
            return qual
            
class BaseBallPlayer(BayesPlayer):
    def __init__(self, num, pos, team,
                 stren, move, fatig,
                 hit_types=con.hit_types,
                 pitch_types=con.pitch_types):
        
        super().__init__(num, pos, team, stren, move, fatig)
        self._swung = False
        self._leadoff = False
        self._steal = False
        self._pick_off = False
        self._pickoff_location = None
        self._onbase = -1 # 1, 2, 3        
        self._hit_types = hit_types
        self._pitch_types = pitch_types

        """The player's pitch possibilities, randomly selected.
        Pitch Type Names, of length k, where 0 < k <= K (== len(PT))
        taken from a random permutation of pitch types.
        """
        pos_k = choice(range(1, len(con.pitch_types)+1))
        self._pitch_types = list(
                np.random.permutation(con.pitch_types)[:pos_k]
        )

    """Return True if a player is injured"""
    def injury_check(self):
        return choice([False, True], p=[.99, .01])

    """Return True if a player commits an error."""
    def error_check(self):
        return choice([False, True], p=[.99, .01])
        
    @property
    def swung(self):
        return self._swung
        
    @property
    def leadoff(self):
        return self._leadoff
        
    @property
    def stealing(self):
        return self._steal
        
    @property
    def pick_off(self):
        return self._pick_off
        
    @property
    def pickoff_location(self):
        return self._pickoff_location
        
    @property
    def cleanup_player(self):
        self._swung = False
        self._leadoff = False
        self._steal = False
        self._pick_off = False
        self._pickoff_location = None

    def make_decision(self, action_type_name, *args):
        sample = choice
        if action_type_name == 'steal':
            self._steal = sample([True, False])
            if self._steal:
                self._leadoff
            return
        elif action_type_name == 'swing':
            self._swung = sample([True, False], p=[.7, .3])
        elif action_type_name == 'leadoff':
            self._leadoff = sample([True, False], p=[.4, .6])
            return
        elif action_type_name == 'pick-off':
            if not args:
                self._pick_off = False
                return
            decision = sample(['y', 'n'], p=[.05, .95])
            if decision == 'n':
                self._pick_off = False
                return
            bases = args[0]
            bases = args[0]
            catch = [None]
            for base, player in bases:
                if base.startswith('third'):
                    catch[0] = player
                else:
                    catch.append((base, player))
            if catch[0] != None:
                catch.reverse()
                p = catch.pop()
                catch.reverse()
                if p.leadoff:
                    self._pick_off = True
                    self._pickoff_location = 'thirdbase'
            else:
                catch.reverse()
                catch.pop()
                catch.reverse()
            if catch:
                if len(catch) == 3:
                    for b, p in catch:
                        if b.startswith('second') and p.leadoff:
                            self._pickoff_location = 'secondbase'
                            self._pick_off = True
                else:
                    # print(catch)
                    b, p = catch[0]
                    if p.leadoff:
                        self._pick_off = True
                        self._pickoff_location = b
            else:
                self._pick_off = False
            return
        else:
            """This is the case for:

            - 'pitch' and 'hit' player decisions.
            """
            action_type = dict(
                [('pitch', self._pitch_types),
                 ('hit', con.hit_types)]
            )
            """ Pitching Type Locations """
            action_loc = {
                'pitch': {
                    'strike': con.strikes,
                    'ball': con.balls
                },
                'hit': {
                    'swing': con.hits
                }
            }        
            action_expected_type = sample(action_type.get(action_type_name))
            possible_location_actions = action_loc.get(action_type_name)
            sub_action_names = list(possible_location_actions.keys())
            sub_action = sample(sub_action_names)
            sub_actions = possible_location_actions[sub_action]
            action_pos = sample(
                range(len(sub_actions))
            )
            """ Return the expected type, location 
            E.g. : 'fastball', ('up', 'away')
            """
            return action_expected_type, sub_actions[action_pos]