#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Written by:  Christopher F. French
        email:  cffrench.writes@gmail.com
         date:  2017
      version:  0.0.1

This is a pre-alpha, broken, version of BayesBall.

--------------------------------------------------------------------------------
This file is part of BayesBall.

BayesBall is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

BayesBall is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with BayesBall.  If not, see <http://www.gnu.org/licenses/>.
--------------------------------------------------------------------------------
"""

"""to do:

[ ] check to see if a player is injured before carrying out an action.
"""

from collections import namedtuple
import numpy as np
from copy import deepcopy
import math

from objects import BayesAction, Action, Outcome, ReferenceClass, __empty__
from base_ball import BaseBall
from context import outcome_records
from player import BaseBallPlayer
from game_exceptions import GameException, GameInjury, GameError
from helpers import categorical_dist, build_subjects, cond_dampen

choice = np.random.choice

def action_prior(**fields):
    prior = namedtuple('Prior', fields.keys())(**fields)
    assert math.isclose(sum(prior), 1, rel_tol=.0001) 
    return prior

    
class StartEvent(BayesAction):
    """Intial event, which can be used for debugging and deque
    manipulation purposes.

    Constructor:
    ===========
    event_tag : str (default='<START>')
    """
    def __init__(self, event_tag='<START>'):
        assert isinstance(event_tag, str)
        start_action = self._build_action_context(
            'start', build_subjects('start')
        )
        start_ref_class = self._build_game_context(None, None)
        super().__init__(start_action, start_ref_class)

        self._happened = True
        self['outcome'] = Outcome(event_tag, event_tag, None)

    def upkeep(self): pass
    def random_triggers(self): pass
    
        
class _X_BayesAction(BayesAction):
    """
    Template for Event Classes during a Bayes Game"""
    def __init__(self, state=None, environment=None,
                 action_name=__empty__, *subject_args):
        
        self.probs = None
        self.prior = action_prior
        subjects = build_subjects(action_name, *subject_args)
        super().__init__(
            self._build_action_context(action_name, subjects),
            self._build_game_context(state, environment)
        )

    def choice(self, probs=None):
        """Returns an outcome based on the probability dictionary *self.probs*,
        which should be intialized using callable property (i.e. a function),
        *self.prior*.

        If *self.probs* = {'A': .3, 'B': .7}, calling *self.choice*
        is the same as calling the *random.choice* function from NumPy:

        > random.choice(['A', 'B'], p=[.3, .7])
        """
        if isinstance(probs, dict):
            prob_dict = probs
        else:
            probs = self.probs if probs == None else probs
            prob_dict = probs._asdict()
        outcomes = list(prob_dict.keys())
        probs_values = list(prob_dict.values())
        return np.random.choice(outcomes, p=probs_values)
    
class CatchEvent(_X_BayesAction):
    
    def __init__(self, state, environment, *subject_args):
        super().__init__(state, environment, 'catch', *subject_args)

    def random_triggers(self):
        """Not Implemented"""
        return NotImplemented
        
    def upkeep(self):
        """Priors for a Catch event:

        - yes (Catch attempt is caught)
        - miss (No catch attempt is/can be made)
        - drop (Catch attempt is made, but dropped)
        (If you edit, make sure to change context.py)
        """
        self.probs = self.prior(yes=.6, miss=.3, drop=.1)
                
    def _perform_action(self):
        self._happened = True
        outcome = self.choice()
        fielder = self.action.subjects.player
        record = outcome_records['catch'][outcome]
        complete_record = record.format(fielder.pos)
        details = dict(fielder=fielder)
        self['outcome'] = Outcome(outcome, complete_record, details)
            
class ThrowEvent(_X_BayesAction):
    """BayesAction class for throwing a baseball from one fielder to another.
    (Note: Player pitch events are handled by a different class, PitchEvent.) 
    """
    def __init__(self, state, environment, *subject_args):
        super().__init__(state, environment, 'throw', *subject_args)
        
    def upkeep(self):
        """Assigns prior probailities directly to Throw event outcomes.
        (see context.py for more information on what these outcomes are.)
        """
        self.probs = self.prior(good=.7, dirt=.1, low=.1, high=.1)

    def random_triggers(self):
        """Not implemented"""
        return NotImplemented
        
    def _perform_action(self):
        self._happend = True
        outcome = self.choice()
        fielder = self.action.subjects.player
        target = self.action.subjects.target
        record = outcome_records['throw'][outcome]
        complete_record = record.format(fielder.pos, target.pos)
        details = dict(player=fielder, target=target)
        self['outcome'] = Outcome(outcome, complete_record, details)
        
class MoveEvent(_X_BayesAction):
    """Move event: whether or not the movement is regular, a stolen
    base, or a caught stolen base, is handled from above, depending
    on whether a tagged event occurs! This means: no choice function
    should be used, at least for now."""
    def __init__(self, state, environment, *subject_args):
        super().__init__(state, environment, 'move', *subject_args)
    def upkeep(self): pass
    def random_triggers(self): pass

    def make_happen(self, outcome='move'):
        self._happened = True
        assert outcome in outcome_records['move']
        to_base = self.action.subjects.to_base
        from_base = self.action.subjects.from_base
        player = self.action.subjects.player
        record = outcome_records['move'][outcome]
        complete_record = record.format(from_base, to_base)
        details = dict(from_base=from_base, to_base=to_base, player=player)
        self['outcome'] = Outcome(outcome, complete_record, details)
        
class TagEvent(_X_BayesAction):   
    def __init__(self, state=None, environment=None, *subject_args):
        super().__init__(state, environment, 'tag', *subject_args)
        
    def upkeep(self):
        self.probs = self.prior(safe=.8, out=.2)

    def random_triggers(self): pass
        
    def _perform_action(self):
        self._happened = True

        outcome = self.choice()
        tagger = self.action.subjects.tagger
        tagged = self.action.subjects.tagged
        record = outcome_records['tag'][outcome]
        complete_record = record.format(tagger.num, tagged.num)
        details = dict(tagger=tagger, tagged=tagged)
        self['outcome'] = Outcome(outcome, complete_record, details)

class ShiftEvent(_X_BayesAction):   
    def __init__(self, state, environment, *subject_args):
        super().__init__(state, environment, 'shift', *subject_args)

    def upkeep(self): pass

    def random_triggers(self): pass
         
    def make_happen(self, shift_option):
        details = {}
        playerstack = self.action.subjects.playerstack
        varstack = self.action.subjects.varstack
        record = outcome_records['shift'][shift_option]
        assert all(isinstance(v, list) for v in [playerstack, varstack])
        if shift_option in ['sub', 'swap']:
            complete_record = record.format(
                playerstack[0], playerstack[1]
            )
            details['new_player'] = playerstack[0]
            details['old_player'] = playerstack[1]
        elif shift_option in ['ASCORE', 'HSCORE', 'out', 'iwalk']:
            complete_record = record
        elif shift_option in ['lead']:
            complete_record = record.format(playerstack[0])
            details['leadoff'] = playerstack[0]
        else:
            raise NotImplemented
        self['outcome'] = Outcome(shift_option, complete_record, details)

class PitchEvent(_X_BayesAction):
    """To do:

    [ ] (SUPER HIGH) write another function -- the "umpire"
        to judge whether a pitch is a strike, or a ball.

        This only makes sense, however, once I get around to
        implementing an actual pitch physics. 

    [ ] (HIGH) the fielder is calculated in a quick and super
        unrealistic way, this needs to be fixed to make
        the simulation more realistic.

    [ ] (HIGH) use bunts/hits/fouls/stikes/balls from context.py
        to determine outcome locations, and then use that
        to help determine fielders, etc. (see above item)
        
    [ ] (HIGH) add in the ability to change base hit priors
        based on player ability / weather conditions, etc.

    [ ] add player multipliers and handle random events

    [ ] modify probs based on ball speed, spin, etc.

    [ ] implement the actual physical simulation for
        pitching and batting events.

    [ ] change code so I'm not reusing 'result' variable,
        in the

            if result == 'hit'

        condition below.
    """
    def __init__(self, state, environment, *subject_args):
        self.possible_outcomes = None
        self._hit = False
        super().__init__(state, environment, 'pitch', *subject_args)
        
    @property
    def hit(self): return self._hit

    def random_triggers(self): pass

    def upkeep(self):
        self.probs = self.prior(wild=.03, balk=.01, hbp=.01,
                                strike=.3, ball=.3, contact=.35)
        
    def _perform_action(self):
        self._happened = True
        batter = self.get('action').subjects.batter
        pitcher = self.get('action').subjects.pitcher
        batter_guess = pitcher.make_decision('pitch') 
        pitcher_decision = pitcher.make_decision('pitch')

        batter.make_decision('swing')
        if batter.swung:
            probs = self.probs._asdict()
            batter_decision = batter.make_decision('hit')
            temp_dict = cond_dampen(probs, ('balk','ball', 'wild'))
            self.probs = self.prior(**temp_dict)
        else:
            probs = self.probs._asdict()
            temp_dict = cond_dampen(probs, ('balk', 'contact'))
            self.probs = self.prior(**temp_dict)
            """Batter doesn't swing'"""
            batter_decision = 'hold'
            
        """This next piece of code is here to see how well the batter
        hit the ball. 

        Right now, it is fairly simple, and is NOT meant to model
        the actual physics of a batting/pitching event. I have been
        working on a module for simulating just that, but it isn't
        being used here, mainly for simplicity sake.
        """
        unit = .1
        batter_mod = 0
        pitcher_mod = 0
        """Checks if batter guessed pitcher's decision'"""
        if pitcher_decision[0] == batter_guess[0]:
            batter_mod+=unit
        else:
            pitcher_mod+=unit
        """checks to see if the batter guessed the right location
        on a grid. This is a super simple way of doing it, and can
        easily be changed to make the batting swing event more
        realistic.
        """
        for x in [0, 1]:
            if pitcher_decision[1][x] == pitcher_decision[1][x]:
                batter_mod+=unit
            else: pitcher_mod+=unit

        new_ball = 0.0 if batter.swung else self.probs.ball+pitcher_mod

        n = sum((self.probs.wild, self.probs.balk, self.probs.hbp,
                 self.probs.strike+pitcher_mod,
                 new_ball,
                 self.probs.contact+batter_mod))
        self.probs = self.prior(
            wild=self.probs.wild/n,
            balk=self.probs.balk/n,
            hbp=self.probs.hbp/n,
            strike=(self.probs.strike+pitcher_mod)/n,
            ball=new_ball/n,
            contact=(self.probs.contact+batter_mod)/n)
            
        
        """For later use:

        This is especially useful for record keeping, e.g., if we want to
        keep track of pitcher pitch types, AND for pitcher/batter learning!
        """
        self.player_choices = (
            batter_decision, pitcher_decision, batter_guess
        )
            
        # print('Current pitch probs: {}'.format(self.probs))
        
        """constants"""
        gs = self.ref_class.state
        strikes = gs.count.strikes
        balls = gs.count.balls
        outs = gs.count.outs
        runners_on = sum(gs.bases)
        locs = self.ref_class.environment.locations
        prior = self.prior

        """priors"""
        hit_type_priors = prior(hit=.4, foul=.45,
                                oop=.1, bunt=.05)

        wild_priors = prior(wp=1)
        balk_priors = prior(blk=1)
        hbp_priors = prior(hbp=1)
        hit_foul_priors = prior(foul=1)
        hit_bunt_priors = prior(bunt=1)
        hit_oop_priors = prior(gdb=.05, hr=.95)
        hit_ball_priors = prior(
            single=.5, double=.35, triple=.149, four=.001
        )

        base_prior_map = dict(
            bunt=hit_bunt_priors, oop=hit_oop_priors,
            foul=hit_foul_priors, hit=hit_ball_priors,
            wild=wild_priors, balk=balk_priors,
            hbp=hbp_priors
        )

        record_type = self.choice()
        precs = outcome_records['pitch']  # pitch records mappings
        record = None
        
        if record_type == 'strike':
            if batter.swung:
                if strikes >= 2:
                    record = precs['strikeout']['swing']
                    record_type = 'strikeout'
                else:
                    record = precs['strike']['swing']
            else:
                if strikes >= 2:
                    record = precs['strikeout']['look']
                    record_type = 'strikeout'
                else:
                    record = precs['strike']['look']
            fielder = locs.home
                    
        elif record_type == 'ball':
            if balls >= 3:
                record = precs['walk']['w']
                record_type =  'walk'
            else:
                record = precs['ball']['b']
            fielder = locs.home
                
        elif record_type == 'contact':
            contact_type = self.choice(hit_type_priors)
            record_type = self.choice(base_prior_map[contact_type])
            record = precs['contact'][contact_type][record_type]
            """quick hack to get fielder"""
            if record in precs['contact']['foul'].values():
                if pitcher_decision[0] == 'fastball' \
                   and batter_decision[0] == 'power':
                    fielder = choice([locs.center, locs.left, locs.right])
                elif batter_decision[0] == 'contact':
                    fielder = choice([locs.first, locs.gap, locs.third])
                else:
                    fielder = locs.home
                
            elif record in precs['contact']['bunt'].values():
                fielder = choice([locs.home, locs.mound, locs.third])
            elif record in precs['contact']['hit'].values():
                if batter_decision[0] == 'power':
                    fielder = choice((locs.left, locs.center, locs.right))
                else:
                    fielder = choice((locs.third, locs.gap,
                                      locs.second, locs.first))
            elif record in precs['contact']['oop'].values():
                fielder = None
            else:
                raise NotImplementedError
                    
        elif record_type == 'wild':
            """need to check if catcher caught the pitch
            for a passed ball to be possible!
            """
            if balls >= 3:
                self._batter_done = True
                record = precs['walk']['w']
            else:
                record_sub_type = self.choice(wild_priors)
                record = precs['wild'][record_sub_type]
            fielder = locs.home

            
        elif record_type == 'hbp':
            record_sub_type = self.choice(hbp_priors)
            record = precs['hbp'][record_sub_type]
            fielder = None
            
        elif record_type == 'balk':
            record_sub_type = self.choice(balk_priors)
            record = precs['balk'][record_sub_type]
            fielder = None
            
        else:
            raise NotImplementedError

        details = dict(ball=None, fielder=fielder)
        self['outcome'] = Outcome(record_type, record, details)

    def build_outcome_from_hit_result(
                self, result, details=None, *players):
        """We don't have enough information, in all cases,
        to return a fully completed outcome, with a filled in
        record.

        These details need to be supplied explicitly using this
        function.

        Example: Triple or double plays. We have to know, after the
        batter gets a hit/bunt whatever, who is out, who runs, ect.
        """
        if not self.happened:
            raise AttributeError('Unable to get pitch record. ' \
                                 + 'Pitch has not yet happened.')

        record = self.possible_outcomes[result]
        complete_record = record.format(*players)

        # Updating Outcome
        self['outcome'] = Outcome(result, complete_record, details)


if __name__ == '__main__':
    from logic import GameState
    Environment = namedtuple(
        'Environment',
        ['weather', 'importance', 'locations']
    )

    location_names = [
        'home', 'homeplate', 'mound',
        'secondbase', 'thirdbase', 'firstbase',
        'second', 'third', 'first',
        'gap', 'shallow',
        'left', 'center', 'right'
    ]

    Locations = namedtuple('Locations', location_names)

    env = Environment(
        weather=None,
        locations=Locations(1,2,3,4,5,6,7,8,9,10, 11, 12, 13, 14),
        importance=0
    )
    gs = GameState()
    gs.update(outs=2, strikes=2, balls=1)
    # print(gs)
    bob = BaseBallPlayer(5, 'DH', 'Gulls', 20, 20, 20)
    alice = BaseBallPlayer(4, '2B', 'Rabbits', 20, 20, 20)
    # print(StartEvent())
    st = StartEvent()
    print(st)

    mv = MoveEvent(gs, env, alice, 1, 2)
    mv.make_happen('steal')
    print(mv)

    tg = TagEvent(gs, env, None, alice, bob)
    print(tg)
    tg.make_happen
    print(tg)

    catch = CatchEvent(gs, env, None, alice)
    print(catch)
    catch.make_happen
    print(catch)

    tr = ThrowEvent(gs, env, None, alice, bob)
    print(tr)
    tr.make_happen
    print(tr)

    shift = ShiftEvent(gs, env, 'Score', [], [])
    print(shift)
    shift.make_happen('ASCORE')
    print(shift)

    pitch = PitchEvent(gs, env, None, alice, bob)
    
    pitch.make_happen
    print(pitch)

    if pitch.hit:
        print('It is a hit, of type: {}'.format(pitch.record))
    for c in pitch.player_choices:
        print(c)
                
