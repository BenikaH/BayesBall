#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  7 22:18:20 2017

@author: christopherfrench
"""
# import math
from itertools import zip_longest, chain
from collections import namedtuple
import numpy as np


actions = ['start', 'pitch', 'throw', 'catch', 'move', 'tag', 'shift']

"""The 'misc' outcomes

I do this so it's easy to add and
modify top-level outcome possibilities.

I use a separate module, outcomes.py,
to view and manipulate these static
structures into something a bit more
probability friendly. 
"""
outcomes = dict(
    [(actions.index('start'),[]),
     (actions.index('pitch'), [
         'strike', 'ball', 'hit', 'error', 'misc'
     ]),
     (actions.index('throw'), [
         'thrown', 'error', 'misc'
     ]),
     (actions.index('catch'), [
         'caught', 'missed', 'error'
     ]),
     (actions.index('move'), [
         'move', 'steal'
     ]),
     (actions.index('tag'), [
         'out', 'safe', 'error'
     ]),
     (actions.index('shift'), [
         'sub', 'strat', 'Score', 'Out'
     ])]
)

game_context_format = ['away_team', 'home_team', 'game_data']
game_data_format = []

action_context_format = dict(
    [(actions.index('start'), []),
     (actions.index('pitch'), [
         'bball', 'pitcher', 'batter'
     ]),
     (actions.index('throw'), [
         'bball', 'player', 'target'
     ]),
     (actions.index('catch'), [
         'bball', 'player'
     ]),
     (actions.index('move'), [
         'player', 'from_base', 'to_base'
     ]),
     (actions.index('tag'), [
         'bball', 'tagger', 'tagged'
     ]),
     (actions.index('shift'), [
         'playerstack', 'varstack'
     ])]
)

"""Return an outcome result key.

Why include action key too? 
Redundancy, for sanity error checking later: we 
have to make sure all actions generate the right 
kinds of outcomes.
"""
def oc_name(action_pos, outcome_pos):
    action = actions[action_pos]
    oc_list = outcomes.get(actions.index(action))
    # if not oc_list[oc_position] is outcomes:
    #    raise Exception("Bad Action, Out_Key: {}".format(action) )
    try:
        return action + "_" + oc_list[outcome_pos]
    except TypeError:
        print(
            '{} and {} not found in {}'.format(
                action, outcome_pos, oc_list
            )
        )
    finally:
        pass
"""
Format dict for record keeping outcomes,
it is quite ugly; but it works, for now.

to do:
=====
[ ] foul tip, strike three; record: 'FT'
[ ] fielder's choie; record: 'FC'
[ ] hit by pitch, batter swings, should result in a strike!
[ ] hit by ptich, batter does/doesn't try to move out of way of ball

"""
outcome_records = dict(
    pitch=dict(
        walk=dict(w='W'),
        balk=dict(blk='BK'),
        hbp=dict(hbp='HBP'),
        strikeout=dict(
            wild='PB', # strike 3, passed ball
            swing='Ks',  # strike 3, swinging
            look='Kc'  # strike 3, looking
        ),
        strike=dict(
            look='Sc',  # Strike, looking
            swing='Ss'  # Strike, swinging
        ),
        ball=dict(
            b='B',  # ball
        ),
        wild=dict(
            wp='WP', # wild pitch  (pitcher mistake)
            pb='PB', # passed ball (catcher mistake)
        ),
        contact=dict(
            bunt=dict(
                bunt='Bunt'  # bunt
            ),
            foul=dict(
                foul='Foul',  # foul ball
            ),
            hit=dict(
                single='Hit:1',  
                double='Hit:2',  
                triple='Hit:3',  
                four='Hit:4'  
            ),
            oop=dict(
                gdb='GDB',  # ground rule double
                hr='HR'  # home run, out of park
            )
        ),
        outs=dict(
            fo='FO:{}',  # fly out: fielder
            uno='U:{}',  # unassisted putout: fielder
            lo='LO:{}',  # line out: fielder
            go='GO:{}'  # ground out: fielder => throw => tagger
        ),
        sack=dict(
            sacf='SF'
        ),
        interf=dict(
            catcher='CI',  # catcher interference
            fielder='I:{}'  # fielder interference: fielder
        )
    ),
    throw=dict(
        good='{}:good:{}',  # generic thrown
        dirt='{}:dirt:{}',  # throw wild
        low='{}:low:{}',  # throw low
        high='{}:high:{}'  # thrown high
    ),
    catch=dict(
        yes='catch:{}',
        drop='dropped:{}',
        miss='missed:{}'
    ),
    move=dict(
        move='{}:move:{}',
        steal='{}:steal:{}',
        caught='{}:caught:{}'
    ),
    tag=dict(
        safe='{}:tagsafe:{}',
        out='{}:tagout:{}'
    ),
    shift=dict(
        sub='{}:sub:{}',
        swap='{}:swap:{}',
        lead='leadoff:{}',
        iwalk='IW',
        HSCORE='<HomeScore>',
        ASCORE='<AwayScore>',
        out='<Out>'
    )
) 
        

      
"""Helper Functions to Build Contexts"""
def arg_dump(*args, form):
    zip_longest(args, form, fill='<MISSING>')

def get_game_context(*args):
    if not len(game_context_format) == len(args):
        _dump_ = arg_dump(args, game_context_format)
        raise Exception("Bad Game Context: %s" % _dump_) 
    return dict(zip(game_context_format, args))

def get_action_context(act, *args):
    this_action_context = action_context_format.get(act, None)
                
    if this_action_context is None:
        raise Exception("Unrecognized Action Type: %s" % act)

    if not len(this_action_context) == len(args):
        _dump_ = arg_dump(args, this_action_context)
        raise Exception("Bad Action Context: %s" % _dump_)
                
    return dict(zip(game_context_format, args))

def to_matrix(V, H):
    return list([(n,m) for m in V] for n in H)

def shallow_flatten(A):
    return list(chain(*A))

    
"""Player and Pitch/Batter mechanics Constants"""
    
""" Strike result possibilities """
K_HORIZ = ['up', 'middle', 'down']
K_VERT = ['in', 'over', 'away']

""" Ball result possibilities """
B_VERT = ['inside', 'outside'] 
B_HORIZ = ['high', 'low']

""" Hit result possibilities """
H_HORIZ = ['outfield', 'infield']
H_VERT  = ['left_line', 'left', 'center', 'right', 'right_line']

""" Foul ball possibilities """
F_HORIZ = ['ahead', 'behind']
F_VERT  = ['catchable', 'stands', 'fence'] 

BU_HORIZ = ['infield', 'catcher', 'foul']
BU_VERT = ['left_line', 'left', 'center', 'right', 'right_line']
       

mat_STRIKES = to_matrix(K_VERT, K_HORIZ)

mat_BALLS = to_matrix(B_VERT, B_HORIZ)

mat_HITS = to_matrix(H_VERT, H_HORIZ)

mat_FOULS = to_matrix(F_VERT, F_HORIZ)

mat_BUNTS = to_matrix(BU_VERT, BU_HORIZ)

strikes = shallow_flatten(mat_STRIKES)

balls = shallow_flatten(mat_BALLS)

hits = shallow_flatten(mat_HITS)

fouls = shallow_flatten(mat_FOULS)

bunts =  shallow_flatten(mat_BUNTS)

"""
Batter/Pitcher Decision Types
"""
pitch_types = ['fastball', 'curveball']

hit_types = ['power', 'contact']



"""FRAGILE!!!"""
def get_action_branch(act_name, outcome_type_name):
    act_name_pos = actions.index(act_name)+1
    act_outcome_pos = outcomes.get(act_name).index(outcome_type_name)
    act_outcome_name = oc_name(act_name_pos, act_outcome_pos)
    kids = oc_tree.getchildren(names=[act_outcome_name])
    catch = {}
    for k in kids[0]:
        catch[k.name] = k.value
    return catch
