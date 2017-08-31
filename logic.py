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
from collections import namedtuple
from context import outcome_records
from helpers import match, match_array

"""Basic namedtuples for building a gamestate"""
Lineup = namedtuple('Lineup', ['batting_order', 'current_pitcher'])
state_labs = ['score','inning','count','bases']
score_lab = ['away', 'home']
Score = namedtuple('Score', score_lab)
inning_lab = ['order', 'inning']
Inning = namedtuple('Inning', inning_lab)
inning_order = ['top', 'bottom']
count_lab = ['strikes', 'balls', 'outs']
Count = namedtuple('Count', count_lab)
bases_lab = ['third', 'second', 'first']
Bases = namedtuple('Bases', bases_lab)
state_types = [Score, Inning, Count, Bases]
game_state_labels = score_lab + inning_lab + count_lab + bases_lab
score_zero  = Score(0, 0)
inning_zero = Inning(inning_order[0], 0)
count_zero  = Count(0, 0, 0)
bases_zero  = Bases(0, 0, 0)

"""Helper Functions."""

def move_n(n, first, second, third, score):
    """Move baserunner helper function.

                 n ::= 1|2|3

    1 for first base, 2 for second, and 3
    for third.


    Movement is ALWAYS conservative: it moves
    each batter at most X bases, where
    X = 1,2,3,4, if, for example, second and
    third is open and first is occcupied with
    a fast runner, even if a single is hit
    and the first baseman COULD get to third,
    the programmer (you) need to send
    ADDITIONAL event_result token to tell the
    runner to then move from second to third.

    Alternatively, player choices about how
    far to run, ability to run, etc. could be
    automated in a call from this function,
    but this is a purely descriptive function
    that updates the gamestate depending on an
    event. 
    """
    assert 0 <= n and n <= 4
    assert 0 <= score
    pre = [first, second, third]
    assert all(x in [0,1] for x in pre)
    hit_result = {
            4: [0, 0, 0],
            3: [0, 0, 1],
            2: [0, 1, first],
            1: [1, first, second]
    }
    post = hit_result.get(n)
    score+=max(
        1+sum(pre)-sum(post), 0
    )  
    return post[0], post[1], post[2], score


class GameState(object):
    """Class for keeping tracking of a baseball state, and
    which then gets updates for each and every BayesEvent,
    represented as a record string.
    """
    __slots__ = ('score', 'inning', 'count', 'bases')

    def __init__(self, **initial_params):
        super().__init__()
        self.score = initial_params.get('score', score_zero)
        self.inning = initial_params.get('inning', inning_zero)
        self.count = initial_params.get('count', count_zero)
        self.bases = initial_params.get('bases', bases_zero)
        
    def __repr__(self):
        args = [*self.score, *self.inning,
                *self.count, *self.bases]
        
        repr_str = 'A:{}-H:{}  {} of {}  S:{}|B:{}|O:{}  3rd:{}|2nd:{}|1st:{}'
        repr_str_full = repr_str.format(*args)
        return repr_str_full.format(self)

    def update(self, reset = False, reset_all = False, **params):
        """Manual updating of gamestate

        Paramaters:
        ==========
        reset_all : Boolean (default: False)

        
        
        Usage: to reset count and change to a runner on
        first, after the home team scores a run, after
        the first batter hit a double:
        
        >>> gs = GameState(second=1)
        >>> gs.update(reset_all = True, first=1, second=0, third=1)
        """
        if reset_all or reset:
            self.count = Count(0, 0, self.count.outs)
            if reset_all:
                self.bases = bases_zero
                self.count = count_zero
            

        state_dict = dict(zip(state_labs, state_types))
        for state_name, state_tuple in state_dict.items():
            catch = {}
            for field in state_tuple._fields:
                try:
                    catch[field] = params[field]
                except:
                    catch[field] = getattr(
                        getattr(self, state_name), field
                    )
            self.__setattr__(
                state_name, state_dict[state_name](**catch)
            )

        assert 0 <= self.score.home
        assert 0 <= self.score.away
        assert 0 <= self.inning.inning
        assert self.inning.order in inning_order
        assert 0 <= (self.count.strikes) <= 3
        assert 0 <= (self.count.balls) <= 4
        assert 0 <= (self.count.outs) <= 3
        assert 0 <= (self.bases.first) <= 1
        assert 0 <= (self.bases.second) <= 1
        assert 0 <= (self.bases.third) <= 1


    def update_from_event_record(self, result):
        """
        Updating GameState from a GameEvent record.
        """
        assert isinstance(result, str)

        """constants"""
        outs = self.count.outs
        balls = self.count.balls
        strikes = self.count.strikes
        first = self.bases.first
        second = self.bases.second
        third = self.bases.third
        home_score = self.score.home
        away_score = self.score.away
        inning = self.inning.inning
        order = self.inning.order
        rel_score = 0

        precs = outcome_records['pitch']
        
        # print('Scoring result: {}'.format(result))

        """Game result record cases:"""
        if result in precs['strike'].values():
            strikes+=1
        elif result in precs['strikeout'].values():
            strikes+=1
        elif result in precs['ball'].values():
            balls+=1
        elif result in precs['walk'].values():
            balls+=1
        elif result == precs['wild']['wp']:
            balls+=1
        elif result in precs['hbp'].values():
            pass
        elif result in precs['contact']['foul'].values():
            if strikes < 2:
                strikes+=1
        elif result in precs['contact']['oop'].values():
            pass
        elif result in precs['contact']['hit'].values():
            pass
        elif result in precs['contact']['bunt'].values():
            pass
        elif match_array(result, precs['outs'].values()):
            pass
        elif result == outcome_records['shift']['out']:
            outs+=1
        elif result == outcome_records['shift']['HSCORE']:
            home_score+=1
        elif result == outcome_records['shift']['ASCORE']:
            away_score+=1
        elif match(result, outcome_records['tag']['safe']):
            pass
        elif match(result, outcome_records['tag']['out']):
            outs+=1
        elif match_array(result, outcome_records['move'].values()):
            if match(result, outcome_records['move']['caught']):
                fromb, tob = result.split(':caught:')

                fromb = int(fromb)
                tob= int(tob)
                
                if fromb == 1:
                    first = 0
                if fromb == 2:
                    second = 0
                if fromb == 3:
                    third = 0
            else:
                if match(result, outcome_records['move']['move']):
                    fromb, tob = result.split(':move:')
                elif match(result, outcome_records['move']['steal']):
                    fromb, tob = result.split(':steal:')
                else:
                    raise ValueError

                fromb = int(fromb)
                tob= int(tob)
                
                if fromb == 1:
                    first = 0
                if fromb == 2:
                    second = 0
                if fromb == 3:
                    third = 0
                if tob == 1:
                    first = 1
                if tob == 2:
                    second = 1
                if tob == 3:
                    third = 1
                if tob == 4:
                    rel_score+=1
        else:
            """
            All the other outcome results won't directly change
            the gamescore, or have already been counted: the
            outcomes like 'ASCORE' or 'HSCORE' or 'OUT' are
            used for the recorder, but not here.

            So they are ignored.
            """
            # print('Warning: ignored record {}'.format(result))

        if order == inning_order[0]:
            away_score+=rel_score
        elif order == inning_order[1]:
            home_score+=rel_score
        else:
            raise ValueError

        outs = 3 if outs > 3 else outs # is this needed!? 
        self.update(home=home_score, away=away_score,
                    outs=outs, strikes=strikes, balls=balls, 
                    first=first, second=second, third=third)
        
if __name__ == '__main__':
    a = GameState()
    a.update(outs=2, order='bottom', strikes=2, first=1)
    print(a)
    a.update_from_event_record('Hit:3')
    print(a)
    a.update_from_event_record('1:move:3')
    print(a)
    
    
