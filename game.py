#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Written by:  Christopher F. French
        email:  cffrench.writes@gmail.com
         date:  2017
      version:  0.1.0

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
import os
from itertools import count, cycle
from collections import deque, namedtuple
from copy import deepcopy
from math import modf

import numpy as np

"""BayesBall modules"""
from logic import GameState
from objects import BayesAction, Outcome
from context import outcome_records
from actions import StartEvent, ThrowEvent, PitchEvent, CatchEvent, \
    TagEvent, MoveEvent, choice, ShiftEvent
from game_exceptions import GameInjury, GameException, GameError
from player import BaseBallPlayer, Positions, pos_from_str
from helpers import categorical_dist, populate_random_roster, \
    gappy_to_probs, match, match_array

records = outcome_records

Environment = namedtuple('Environment',
                         ['weather', 'importance',
                          'locations', 'batter', 'pitcher'])
GameRecord = namedtuple('GameRecord', ['time', 'outcome'])
Team = namedtuple('Team', ['name', 'lineup', 'roster'])
location_names = ('home', 'homeplate', 'mound',
                  'secondbase', 'thirdbase', 'firstbase',
                  'second', 'third', 'first',
                  'gap', 'shallow',
                  'left', 'center', 'right')
Locations = namedtuple('Locations', location_names)
NullLocations = Locations(*[None]*len(location_names))

"""Currently not implemented"""
BaseBall = namedtuple('BaseBall',['velocity', 'angle', 'z_spin', 'y_spin'])

class _BayesGame(deque):
    """Base Game Class Template.

    _BayesGame is a base class for BayesGame.
    It subclasses the class deque from the Python
    standard library 'collections'.
    """
    def __init__(self, start_record):
        super().__init__([start_record])

class BayesGame(_BayesGame):
    """Base Game Class"""
    def __init__(self, away_team, home_team, time=0):
        super().__init__(GameRecord(time, StartEvent().result))

        """For pre-alpha dev use only!

        We use dummy teams and players as defaults
        """
        if away_team == None or home_team == None:
            home_team, away_team = populate_random_roster(
                25, BaseBallPlayer, Positions, Team
            )
            
        self._away = away_team
        self._home = home_team
        self.current_time = time
        self.gamestate = GameState()
        self._winmsg = None

    def add_record(self, rec, time=None, debug=False):
        """Add a record to BayesGame instance (a deque)

        rec : str
        time : Number (default: None) [Currently not Implemented]
        debug : Boolean (default: False)
        """
        assert isinstance(rec, str)
        time = self.current_time if time == None else time
        if debug:
            print('Adding {} to deque'.format(rec))
        self.extendleft([GameRecord(time, rec)])

    @property
    def win_msg(self):
        """Returns a message detailing winning state information."""
        return self._winmsg

    @property
    def home(self):
        """Returns the current Home team (default: namedtuple)."""
        return self._home

    @property
    def away(self):
        """Returns the current Away team (default: namedtuple)"""
        return self._away

    def result(self):
        """This is used to return the result of a full game, usefull
        later when full seasons or days are simulated.
        
        Returns:
         1, if the home team won.
         0, if the away team won.
        -1, if the game was cancelled, or delayed.
        """
        return NotImplemented

    def play_next_state(self, *args, **kwargs):
        """Main recursive function that transitions to the next complete
        game state, as a sequence of Bayes actions, and 'meta' states,
        including events like the substitution or swaping of players.
        """
        raise NotImplementedError

    def upkeep_state(self, **game_init):
         """Performs, if required, upkeep to the gamestate and/or teams."""
         raise NotImplementedError
         
    def win(self):
        """Returns True if the current state is a winning state, False otherwise."""
        raise NotImplementedError


class BaseBallGame(BayesGame):
    """Main Class to Play a *Complete* Baseball Game"""
    def __init__(self, away_team, home_team, debug=False):
        super().__init__(away_team, home_team)
        self.batter = None
        self.pitcher = None
        self.locations = NullLocations
        self.home_next_bat = cycle(range(0, 9))
        self.away_next_bat = cycle(range(0, 9))
        self._home_pos = 0
        self._away_pos = 0
        self._batter_done = True
        self.debug = debug
        self.debug_msgs = []
        self.initial_upkeep()
        

    def initial_upkeep(self):
        """Populates team lineups."""
        def place_players(linup):
            """Helper function to place players on the field depending
            on their position. 

            Paramaters:
            ==========
            linup: list

            - linup shoudl be a list of BaseBallPlayer instances
            """
            pos_to_loc = {'C': 'home', '1B': 'first', '2B': 'second',
                          '3B': 'third', 'SS': 'gap', 'LF': 'left',
                          'CF': 'center', 'RF': 'right', 'P': 'mound'}
            locs = self.locations._asdict()
            for p in linup:
                for pos_name in pos_to_loc.keys():
                    if p.pos == pos_from_str(pos_name):
                        locs[pos_to_loc.get(pos_name)] = p
            self.locations = Locations(**locs)

        if self.gamestate.inning.order == 'top':
            place_players(self.home.lineup)
        else:
            place_players(self.away.lineup)
            
    @property
    def batter_finished(self):
        """Returns True if the current batter is finished batter,
        and False otherwise.
        """
        return self._batter_done
            
    def sub_players(self, old, new):
        """(Experimental.) This function substitutes the Player *old*
        in the current *self.lineup.lineup* with the Player *new*
        on the teams roster, *self.lineup.roster*.
        """
        if (old in self.away.lineup) and (new in self.away.roster):
            side = 'away'
        elif (old in self.home.lineup) and (new in self.home.roster):
            side = 'home'
        else:
            error_msg = 'Players {} and {} not in lineups'
            raise IndexError(error_msg.format(old))
            
        old_pos = old.pos
        team = getattr(self, side)
        old_lineup = team.lineup
        new_roster = getattr(team, side+'_bench')
        old_index = old_lineup.index(old)
        new_index = new_roster.index(new)
        old.pos('Bench')
        new._pos = old_pos
        name = team.name
        new_roster[new_index] = old
        old_lineup[old_index] = new
        self.__setattr__('_'+side, Team(name, old_lineup, new_roster))
        
    def swap_players(self, old, new):
        """(Experimental.) This function swaps the Player *old*
        in the current *self.lineup.lineup* with the Player *new*
        which is also in the teams lineup.
        """
        assert all(x in self.away.lineup for x in [old, new]) \
            or all(x in self.home.lineup for x in [old, new])
        pos_old = old.pos
        pos_new = new.pos
        old._pos = pos_new
        new._pos = pos_old
        self.initial_upkeep()

    def win(self, I):
        """Returns True if the current game is over, False otherwise. """
        win = False
        scores = self.gamestate.score
        if I >= 9 and (scores.home > scores.away):
            win = True
            winner = self.home.name
            loser = self.away.name
            diff = scores.home-scores.away
        elif I >= 9.5 and (scores.home < scores.away):
            win = True
            winner = self.away.name
            loser = self.home.name
            diff = scores.away-scores.home
        else:
            return False
        msg_template = "{} beat {} by {} points!"
        self._winmsg = msg_template.format(winner, loser, diff)
        return True
        
    def action_move(self, player, n, m, option='move'):
        """Method to construct a Move BayesEvent"""
        assert isinstance(n, int)
        assert isinstance(m, int)
        move = self.play_next_state(MoveEvent, option, player, n, m)
        if self.debug:
            catch = []
            catch.append('move event \n{}'.format(move.outcome))
            catch.append('*'*80)
            self.debug_msgs.extend(catch)
        return move

    def action_tag(self, tagger, tagged):
        """Method to construct a Tag BayesEvent"""
        tag = self.play_next_state(TagEvent, None, None, tagger, tagged)
        if self.debug:
            catch = []
            catch.append('tag event \n{}'.format(tag.outcome))
            catch.append('tag probs \n{}'.format(tag.probs))
            catch.append('*'*80)
            self.debug_msgs.extend(catch)
        return tag
            
    def action_throw(self, thrower, location):
        """Method to construct a Throw BayesEvent"""
        throw = self.play_next_state(ThrowEvent, None,
                                     None, thrower, location)
        if self.debug:
            catch = []
            catch.append('throw event \n{}'.format(throw.outcome))
            catch.append('throw event \n{}'.format(throw.probs))
            catch.append('*'*80)
            self.debug_msgs.extend(catch)
        return throw
            
    def action_catch(self, ball, location):
        """Method to construct a Catch BayesEvent"""
        catch = self.play_next_state(CatchEvent, None, ball, location)
        if self.debug:
            bucket = [] 
            bucket.append('catch event \n{}'.format(catch.outcome))
            bucket.append('catch probs \n{}'.format(catch.probs))
            bucket.append('*'*80)
            self.debug_msgs.extend(bucket)
        return catch

    def action_shift(self, option, pstack=[], vstack=[]):
        """Method to construct a Shift BayesEvent"""
        shift = self.play_next_state(ShiftEvent, option, pstack, vstack)
        if self.debug:
            catch = []
            catch.append('shift event \n{}'.format(shift.outcome))
            catch.append('*'*80)
            self.debug_msgs.extend(catch)
        return shift
        
    def play_next_state(self, action_cls, shift_option, *subjects):
        """Main method for transitioning between gamestates

        action_cls : BayesEvent class
        shift_option : str
        subjects : list
        """
        assert action_cls.isaction(action_cls.__name__)
        basenames = ['firstbase', 'secondbase', 'thirdbase']
        global records
        """Helper functions."""
        def play_hit(N, batter_move=True):
            """Most conservative movement of batter to base N.

            Paramaters:
            ==========
            N : int
            batter_move : bool (default: True)
            """
            assert isinstance(N, int)
            if self.locations.thirdbase:
                self.action_move(self.locations.thirdbase, 3, 4)
            if self.locations.secondbase:
                self.action_move(self.locations.secondbase, 2, min(4, N+2))
            if self.locations.firstbase:
                self.action_move(self.locations.firstbase, 1, min(4, N+1))
            if batter_move:
                self.action_move(self.batter, 0, N)
            self._batter_done = True
            
        def throw_arc(thrower, target, tagged, *second_throw_args):
            """Event sequence: hrow -> Tag -> [Throw -> Tag]"""
            global records
            throw = self.action_throw(thrower, target)
            if throw.result == 'good':
                catch = self.action_catch(None, target)
                if catch.result == 'yes':
                    self.action_tag(target, tagged)
                    if second_throw_args:
                        thrower = second_throw_args[0]
                        target = second_throw_args[1]
                        tagged = second_throw_args[2]
                        throw_arc(thrower, target, tagged)

        def catcher_catch_pitch(pitch_result):
            """Main sequence for Catcher catching a pitch"""
            c_catch = self.action_catch(None, catcher)
            homesteal = False
            stealers = []
            walk = pitch_result == 'walk'
            
            for n in basenames:
                if getattr(self.locations, n):
                    player = getattr(self.locations, n)
                    if player.stealing:
                        stealers.append((n, player))
                
            if c_catch.result == 'yes' and walk:
                        pass
            elif c_catch.result == 'yes' and not walk:
                if stealers:
                    runner = None
                    base = None
                    n = -1
                    m = -1
                    for basename, player in stealers:
                        if 'thirdbase' == basename:
                            runner = player
                            n = 3
                            m = 4
                            homesteal = True
                            break
                        if 'secondbase' == basename:
                            runner = player
                            n = 2
                            m = 3
                            base = 'third'
                    if runner == None:
                        runner = stealers[0][1]
                        n = 1
                        m = 2
                        base = 'second'
                    if homesteal:
                        tag = self.action_tag(catcher, runner)
                    else:
                        if base == 'second':
                            target = self.locations.second
                        else:
                            target = self.locations.third
                        throw = self.action_throw(catcher, target)
                        if throw.result == 'yes':
                            tag = self.action_tag(target, runner)
                        else:
                            tag = None
                    if tag:
                        if tag.result == 'safe':
                            self.action_move(runner, n, m, option='steal')
                        if tag.result == 'out':
                            self.action_move(runner, n, m, option='caught')
                    else:
                        self.action_move(runner, n, m, option='steal')

        """Action instantiation."""
        action = action_cls(
            self.gamestate,
            Environment(
                weather=None, locations=self.locations,
                importance=0, batter=self.batter,
                pitcher=self.pitcher
            ),
            *subjects
        )
        
        if action.has_name('PitchEvent'):
            pitch = action            
            """First: check if runners will leadoff/steal"""
            bases = []
            for n in basenames:
                if getattr(self.locations, n):
                    player = getattr(self.locations, n)
                    player.make_decision('leadoff')
                    player.make_decision('steal')
                    bases.append((n, player))
            self.pitcher.make_decision('pick-off', bases)
            if self.pitcher.pick_off:
                """If there is a pitch-out, after the throw/catch/tag
                sequence is over, the play ends and a new pitch event
                has to start.
                """
                loc = self.pitcher.pickoff_location
                base = loc.split('base')[0]
                fielder = getattr(self.locations, base)
                runner = getattr(self.locations, loc)
                throw_arc(self.pitcher, fielder, runner)
                record = 'pitchout:{}'.format(fielder.pos)
                pitch['outcome'] = Outcome('pitch_out', record, {})
                return pitch
                
            pitch.make_happen

            contacts = records['pitch']['contact']
            catcher = self.locations.home
            
            if pitch.result in ['balk', 'hbp']:
                """Pitcher balks or batter is hit by pitch"""
                if self.locations.thirdbase:
                    self.action_move(self.locations.thirdbase, 3, 4)
                if self.locations.secondbase:
                    self.action_move(self.locations.secondbase, 2, 3)
                if self.locations.firstbase:
                    self.action_move(self.locations.firstbase, 1, 2)
                if pitch.result == 'hbp':
                    self.action_move(self.batter, 0, 1)
                    self._batter_done = True
                self.add_record(pitch.record)
                
            elif pitch.result == 'strike':
                self.add_record(pitch.record)
                catcher_catch_pitch(pitch.record)
                
            elif pitch.result == 'strikeout':
                self._batter_done = True
                self.add_record(pitch.record)
                self.action_shift('out')
                catcher_catch_pitch(pitch.record)
                
            elif pitch.result == 'ball':
                self.add_record(pitch.record)
                catcher_catch_pitch(pitch.record)
                
            elif pitch.result == 'walk':
                self._batter_done = True
                if self.locations.firstbase:
                    if self.locations.secondbase:
                        if self.locations.thirdbase:
                            self.action_move(self.locations.thirdbase, 3, 4)
                        self.action_move(self.locations.secondbase, 2, 3)
                    self.action_move(self.locations.firstbase, 1, 2)
                self.action_move(self.batter, 0, 1)
                self.add_record(pitch.record)

            elif pitch.result == 'wild':
                """wild pitch"""
                if self.locations.firstbase:
                    if self.locations.secondbase:
                        if self.locations.thirdbase:
                            self.action_move(self.locations.thirdbase, 3, 4)
                        self.action_move(self.locations.secondbase, 2, 3)
                    self.action_move(self.locations.firstbase, 1, 2)
                self.add_record(pitch.record)
                if self.gamestate.count.balls == 4:
                    self._batter_done = True
                    
                
            elif pitch.result in contacts['hit']:
                hit = pitch
                fielder = hit.outcome.details['fielder']
                ball = hit.outcome.details['ball']
                catch = self.action_catch(ball, fielder)
                if catch.result == 'yes':
                    """NOT REALISTIC YET
                    
                    Also, what about attempts at
                    double/triple plays?

                    ALSO: if the ball is GROUNDBALL,
                    runners can still run! ... so sacflys,
                    etc. are not possible at the moment!!!
                    """
                    rec_dict = records['pitch']['outs']
                    record = choice(list(rec_dict.values()))
                    self.add_record(record.format(fielder.pos))
                    self.action_shift('out')
                    self._batter_done = True
                else:
                    """WARNING!
                    I'm ignoring miss/drop distinction.
                    
                    ALSO: if dropped, the fielder
                    should get an error!

                    ALSO: runners should be able to attempt
                    to keep running!
                    """
                    N = int(hit.record.split(':')[1])
                    play_hit(N)
                    self._batter_done = True
                    self.add_record(hit.record)

            elif pitch.result == 'gdb':
                hit = pitch
                """Ground hit double"""
                if self.locations.thirdbase:
                    self.action_move(self.locations.thirdbase, 3, 4)
                if self.locations.secondbase:
                    self.action_move(self.locations.secondbase, 2, 4)
                if self.locations.firstbase:
                    self.action_move(self.locations.firstbase, 1, 3)
                self.action_move(self.batter, 0, 2)
                self.add_record(hit.record)
                self._batter_done = True

            elif pitch.result == 'hr':
                hit = pitch
                """Homerun"""
                play_hit(4)
                self.add_record(hit.record)
                self._batter_done = True
                
            elif pitch.result == 'bunt':
                hit = pitch
                fielder = hit.outcome.details['fielder']
                ball = hit.outcome.details['ball']
                catch = self.action_catch(ball, fielder)
                if catch.result == 'yes':
                    record = records['pitch']['outs']['go']
                    self.add_record(record.format(fielder.pos))
                    self.action_shift('out')
                    self._batter_done = True
                else:
                    play_hit(1)
                    self.add_record(hit.record)
                        
            elif pitch.result == 'foul':
                hit = pitch        
                fielder = hit.outcome.details['fielder']
                ball = hit.outcome.details['ball']
                catch = self.action_catch(ball, fielder)
                if catch.result == 'yes':
                    record = records['pitch']['outs']['fo']
                    self.add_record(record.format(fielder.pos))
                    self.action_shift('out')
                    self._batter_done = True
                else:
                    self.add_record(hit.record)
                self.add_record(hit.record)
            
            else:
                err_msg = '\nUnknown {}\n\t result: {}\n\t record: {}\n'
                raise ValueError(
                    err_msg.format(pitch.name, pitch.result, pitch.record)
                )

            """Tail end of PitchEvent:

            Now we have to check if a triple/double play occured.


            THIS PART IS BROKEN.
            """
            initial_outs = self.gamestate.count.outs
            initial_runners = sum(self.gamestate.bases)
            FLYO = -1
            SCORE = False
            GIDP = False
            out_events = []
            triple_possible = (initial_outs < 1) \
                              and (initial_runners > 1)
            double_possible = (initial_outs < 2) \
                              and (initial_runners > 0)
            for x, grec in enumerate(self):
                splitrec = grec.outcome.split(':')
                if splitrec[0] == 'FO':
                    FLYO = x
                    out_events.append((grec.time, grec.outcome.split(':')[1]))
                elif grec.outcome in ['ASCORE', 'HSCORE']:
                    SCORE = True
                elif grec.outcome in ['PB', 'Ks', 'Kc', 'FT']:
                    out_events.append((grec.time, self.locations.home.pos))
                elif len(splitrec) > 1 and splitrec[1] == 'out':
                    firstplayernum = splitrec[0].split('<')[1]
                    secondplayernum = splitrec[2].split('>')[0]
                    out_events.append(
                        (grec.time, firstplayernum, secondplayernum)
                    )
                elif splitrec[0] in ['LO', 'FC', 'GO']:
                    out_events.append((grec.time, splitrec[1]))
                    if splitrec[0] == 'FC':
                        GDIP = True

            if (FLYO > -1) and SCORE:
                self.add_record('SF', self[FLYO].time)

            """In baseball, triple/double plays are recorded like:

            3-6*-5, where 6* is a position that is a transition
            between positions 3 and 5, but player 6 did NOT make
            an out.

            Below, I just record the players who make outs.

            Good enough for now ... BUT STILL BROKEN
            """
            if triple_possible and len(out_events) == 3:
                out_events.sort()
                playernums = []
                max_time = 0
                for t, p in out_events:
                    playernums.extend(p)
                    max_time = max(t, max_time)
                num = len(playernums)
                assert num > 0 and 5 > num
                records = {
                    1: 'TP:{}',
                    2: 'TP:{}-{}',
                    3: 'TP:{}-{}-{}',
                    4: 'TP:{}-{}-{}-{}'
                }
                rec = records[num]
                self.add_record(rec.format(*playernums), max_time)
            if double_possible and len(out_events) == 2:
                out_events.sort()
                playernums = []
                max_time = 0
                for t, p in out_events:
                    playernums.extend(p)
                    max_time = max(t, max_time)
                num = len(playernums)
                assert num > 0 and 4 > num
                records = {
                    1: 'DP:{}',
                    2: 'DP:{}-{}',
                    3: 'DP:{}-{}-{}'
                }
                rec = records[num]
                self.add_record(rec.format(*playernums), max_time)

                if GIDP:
                    self.add_record(rec.format('GIDP'), max_time)

            return pitch
            
        elif action.has_name('StartEvent'):
            start = action
            self.add_record(start.record)
            return start

        elif action.has_name('CatchEvent'):
            catch = action
            try:
                catch.make_happen
                self.add_record(catch.record)
                if catch.result == 'error':
                    raise GameError('catch', catch)
                
                return catch
            except GameError as ge:
                """BROKEN, needs to be fixed.

                Originally, the below code was going to be used
                for when a catch is missed, but fielders still
                need to throw out runners.
                """

                # fresh copy of locations!
                locs = self.locations
                """Update where the runners are heading next
                right now: they automatically try to get to the
                next base when there is an error, which is NOT
                entirely realistic.
                """
                runners = []
                if self.locations.firstbase:
                    runners.append('first')
                    self.action_move(self.locations.firstbase, 1, 2)
                    end_base = 'second'
                if self.locations.secondbase:
                    runners.append('second')
                    self.action_move(self.locations.secondbase, 2, 3)
                    end_base = 'third'
                if self.locations.thirdbase:
                    runners.append('third')
                    self.action_move(self.locations.thirdbase, 3, 4)
                    end_base = 'home'
                if 'third' in runners:
                    relevant_base = 'third'
                else:
                    relevant_base = choice(runners)

                tagged = getattr(loc, relevant_base+'base')
                target = getattr(loc, relevant_base)
                if ge.parent_name == 'pitch':
                    if ge.event.action.action  == 'catch':
                        """
                        Fielder dropped the ball!
                        """
                        fielder = ge.event.outcome.details['fielder']
                        outfield = ['LF', 'CF', 'RF']
                        infield = ['3B', 'SS', '2B', '1B']
                        of_nums = [Postions.index(s) for s in outfield]
                        in_nums = [Postions.index(s) for s in infield]
                        left_side_outfield = [
                            self.locations.left, self.locations.center
                        ]
                        right_side_outfield = [
                            self.locations.center, self.locations.right
                        ]

                        # probabilities for which new fielder
                        # picks up the ball that the old fielder
                        # missed/dropped due to an error.
                        # to do: REWRITE when a proper baseball
                        #        physics / hit detection is added.

                        pr_cf_of = 16.66667
                        pr_lf_of = pr_cf_of * 2
                        pr_rf_of = 1-pr_cf_of-pr_lf_of
                        """
                        These are cases where an infielder, e.g. SS
                        missed a ball, and then an outfielder has
                        to pick it up.

                        Reminder: super important to add a time penalty
                        for passed balls!

                        also: fielder is the player who errored!
                        """
                        if fielder.pos in in_nums[:2]:
                            thrower = categorical_dist(
                                left_side_outfield,
                                *[pr_lf_of, pr_cf_of],
                                predict=True
                            )
                        elif fielder.pos in in_nums[1:]:
                            thrower = categorical_dist(
                                right_side_outfield,
                                *[pr_cf_of, pr_rf_of],
                                predict=True
                            )
                        elif fielder.pos in of_nums[:2]:
                            thrower = self.locations.gap
                            throw_arc(thrower, target, tagged)
                        elif fielder.pos in of_nums[1:]:
                            thrower = self.locations.second
                            throw_arc(thrower, target, tagged)
                        else:
                            # to do: check if fielder is injured ...
                            #        if so: runner gets the base w/o tag
                            thrower = fielder
                            if target == fielder:
                                self.action_tag(target, tagged)
                            else:
                                throw_arc(thrower, target, tagged)
                            for base_name, runner in runners:
                                if base_name == 'third':
                                    tagged = runner
                            if target == None:
                                target = choice(runners)
                        catch['outcome'] = Outcome(
                            catch.outcome.result,
                            'E:{}'.format(fielder),
                            catch.outcome.details
                        )
                if ge.parent_name == 'throw':
                    if ge.event.action.action  == 'catch':
                        fielder = ge.event.outcome.details['fielder']
                        if target == fielder:
                            # to do: add time penalty!
                            self.action_tag(fielder, tagged)
                        else:
                            throw_arc(fielder, target, tagged)
                        catch['outcome'] = Outcome(
                            catch.outcome.result,
                            'E:{}'.format(fielder),
                            catch.outcome.details
                        )
            """End of except case for CatchEvent."""
            
        elif action.has_name('TagEvent'):
            tag = action
            tag.make_happen
            tagger = tag.outcome.details['tagger'],
            tagged = tag.outcome.details['tagged']
            if tag.result in ['out']:
                self.action_shift('out')
            self.add_record(tag.record)
            return tag
          
        elif action.has_name('ShiftEvent'):
            shift = action
            shift.make_happen(shift_option)
            if shift.result == 'lead':
                player = shift.outcome.details['leadoff']
                player._leadoff = True

            elif shift.result == 'sub':
                old_player = shift.outcome.details['old_player']
                new_player = shift.outcome.details['new_player']
                self.sub_players(old_player, new_player)

            elif shift.name == 'swap':
                old_player = shift.outcome.details['old_player']
                new_player = shift.outcome.details['new_player']
                self.swap_players(old_player, new_player) 

            else:
                pass
            
            self.add_record(shift.record)
            return shift

        elif action.has_name('ThrowEvent'):
            throw = action
            throw.make_happen
            self.add_record(throw.record)
            return throw
                
        elif action.has_name('MoveEvent'):
            move = action
            move.make_happen(shift_option)
            
            base_dict = {1: 'firstbase', 2: 'secondbase',
                         3: 'thirdbase', 0: None, 4: None}

            fromb = base_dict[move.outcome.details['from_base']]
            tob = base_dict[move.outcome.details['to_base']]
            runner = move.outcome.details['player']
            loc = self.locations._asdict()
            if move.result in ['move', 'steal']:
                if fromb:
                    if fromb == base_dict[3]:
                        if self.gamestate.inning.order == 'top':
                            self.action_shift('ASCORE')
                        else:
                            self.action_shift('HSCORE')
                    loc[fromb] = None
                if tob:
                    loc[tob] = runner
                    
            elif move.result == 'caught':
                if tob:
                    loc[tob] = None
                loc[fromb] = None
                    
            else:
                raise NotImplementedError
                
            self.locations = Locations(**loc)
            self.add_record(move.record)
            return move

    @property
    def change_lineup(self):
        """This is the central function that makes sure
        the next batter gets to bat after a walk/hit/strikeout,
        or hit-by-pitch, etc.

        WARNING: it is up to the coder to manually add the
        piece of code

            self._batter_done = False

        when a batter should be finished after a play.
        """
        order = self.gamestate.inning.order
        if order == 'top':
            if self.batter_finished:
                self.gamestate.update(reset=True)
                self._away_pos = next(self.away_next_bat)
                self.batter = self.away.lineup[self._away_pos]
                self._batter_done = False
            for p in self.home.lineup:
                if p.pos == Positions.index('P'):
                    self.pitcher = p
                    
        elif order == 'bottom':
            if self.batter_finished:
                self.gamestate.update(reset=True)
                self._home_pos = next(self.home_next_bat)
                self.batter = self.home.lineup[self._home_pos]
                self._batter_done = False
            for p in self.away.lineup:
                if p.pos == Positions.index('P'):
                    self.pitcher = p
        else:
            raise Exception('Bad Inning Order {}'.format(order))
    
    def upkeep(self, I):
        """Updates the game information at the start of a new inning."""
        self.gamestate.update(reset_all=True)
        order = 'top' if (modf(I)[0] == 0.0) else 'bottom'
        self.gamestate.update(order=order, inning=I)
            
    @property
    def play(self, debug=True):
        """Play through a pitch event."""
        self.change_lineup
        pitch = self.play_next_state(
            PitchEvent,
            None,
            None,            # BaseBall class instance!
            self.pitcher,
            self.batter
        )
        if self.debug:
            catch = []
            catch.append('pitch event: \n{}'.format(pitch.outcome))
            catch.append('pitch probs: \n{}'.format(pitch.probs))
            catch.append('*'*80)
            self.debug_msgs.extend(catch)
        history = []
        self.reverse()
        start = self.popleft()
        self.reverse()
        self.append(start)
        while self[0].outcome != '<START>':
            rec = self.popleft()
            self.gamestate.update_from_event_record(rec.outcome)
            history.append(rec.outcome)
        assert len(self) == 1
        return history 

    def manage(self):
        """Eventually, this method will define a means with which
        the ShiftEvent options 'swap' and 'sub' can be used--either
        through a user-based UX, or an agent-based manager.

        Current Status: NotImplemented
        """
        return NotImplementedError
        

def play_baseball_game():
    """Watch a baseball game get played."""
    os.system('clear||clr')
    game = BaseBallGame(None, None, True)
    innings = count(1, .5)
    for I in innings:
        game.upkeep(I)
        if game.win(I):
            break
        while game.gamestate.count.outs < 3:
            game.play
            if game.debug:
                while game.debug_msgs:
                    print(game.debug_msgs.pop())
                print('*'*80)
            print(game.gamestate)
            print('Batter: {} \t Pitcher: {}'.format(
                    game.batter, game.pitcher)
            )
            print('*'*80)
            input('continue to next state')
            os.system('clear||clr')
        
    input('\n bayesball instance finished. \n press enter to exit.')

if __name__ == '__main__':
    play_baseball_game()