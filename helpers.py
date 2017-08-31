#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from numpy.random import choice, permutation
import context as con
from collections import namedtuple
from copy import deepcopy


"""
misc: needs a home?
"""
def bbdata(velocity=86, angle=45, z_spin=.2, y_spin=.2):
    return BaseBall(
        velocity=velocity, angle=angle,
        z_spin=z_spin, y_spin=y_spin
    )

    
def inverse_logistic(Wa,Xa,b):
    terms = np.inner([Wa], [Xa]) + b
    bot = 1-np.exp(terms)
    return -1/float(bot)

def avg(*args):
    if all(isinstance(x, Number) for x in args):
        N = len(args)
        return sum(args)/float(N)
    else:
        return NotImplemented

def sample_on(name, *args):
    if name == 'scalar':
        # needs to be fixed
        return 80. * np.random.sample() + 20.
    elif name == 'trunc_mu':
        mu = args[0]
        return truncnorm.rvs(20.-mu, 100.-mu, loc=mu)
    elif name == 'choice':
        return np.random.choice(args),
    elif name == 'nn_out':
        return NotImplemented
    else:
        return NotImplemented



def match(rec, rec_format):
    format_splits = rec_format.split(':')
    rec_splits = rec.split(':')
    for s in format_splits:
        if s in rec_splits:
            return True
    return False

def match_array(rec, array):
    for a in array:
        if match(rec, a):
            return True
    return False

        
"""Helpers for game.py:
- categorical_dist
- gappy_to_probs
- populate_random_roster
"""
    
def build_subjects(action, *subjects):
    if subjects is None:
        return namedtuple('Subjects')
    fieldnames = con.action_context_format.get(
            con.actions.index(action)
    )
    try:
        assert len(fieldnames) == len(subjects)
    except:
        print(fieldnames, subjects)
    Subjects = namedtuple('Subjects', fieldnames)
    return Subjects(*subjects)

    
"""Conditional probabilities over dict probs.
- probs: dict, e.g. {'e1': .6, 'e2': .4}
- sub: list, subset of probs w/ raised values.
- cond: assumes 1 >= cond >= 0; cond is
the prob given to all the events NOT in sub. 

Use this with categorical_dist when predict=False.
"""
def cond_dampen(probs, sub = [], cond = 0):
    if (1 >= cond) and (cond >= 0):
        assert all(event in probs.keys() for event in sub)
        assert len(probs) >=  len(sub)
        probs = deepcopy(probs)
        scalar_norm = 0
        for event in sub:
            scalar_norm += probs[event]
            probs[event] = cond
        num_not_sub = len(probs) - len(sub)
        norm = scalar_norm / float(num_not_sub)     
        for lab, prob in probs.items():
            if lab not in sub:
                probs[lab] += norm
    else:
        print('Bad Conditional Dampening over Probs.')
    return probs

def categorical_dist(labels, *scalars, predict=False):
    N = len(scalars)
    S = float(sum(scalars))
    probs = [0]*N
    for x in range(N-1):
        probs[x] = scalars[x]/S
    probs[N-1] = 1-sum(probs)
    if predict:
        return choice(labels, p=probs)
    prob_dist = dict(zip(labels, probs))
    return prob_dist

def gappy_to_probs(gaps, prob_dist):
    probs = {}
    for name, vals in gaps.items():
        if vals != []:
            probs[name] = prob_dist[name]
    # returns the conditional prob
    return categorical_dist(
        probs.labels(),
        *list(probs.values()),
        predict=True
    )

def populate_random_roster(rostersize, player_cls, Positions, Team):
    assert rostersize >= 9
    assert isinstance(Positions, list)
    # randomly choose twenty five numbers, for player numbers.
    def nums():
        rand_nums = permutation(
            list(frozenset(range(100))-set([42, 0]))
        )
        return list(rand_nums)[:rostersize]
    # assuming no designated hitter, for now.
    home_nums = nums()
    away_nums = nums()
    home_lineup = []
    away_lineup = []
    home_bench = []
    away_bench = []
    away_name = 'Bellevue'
    home_name = 'Ballard'
    home_pit = None
    away_pit = None
    for x, pos in enumerate(Positions[1:10]):
        home_lineup.append(
            player_cls(
                home_nums[x], pos, home_name, 50, 20, 100
            )
        )
        away_lineup.append(
            player_cls(
                away_nums[x], pos, away_name, 50, 20, 100
            )
        )
        if pos == 'P':
            n = len(home_lineup)
            home_pit = home_lineup[n-1]
            away_pit = away_lineup[n-1]
    for z in range(9, 25):
        home_bench.append(
            player_cls(home_nums[z], 'Bench', home_name, 50, 20, 100)
        )
        away_bench.append(
            player_cls(away_nums[z], 'Bench', away_name, 50, 20, 100)
        )

    home_lineup = permutation(home_lineup)
    away_lineup = permutation(away_lineup)

    home = Team(
        home_name,
        home_lineup,
        home_bench
    )
    away = Team(
        away_name,
        away_lineup,
        away_bench
    )    
    return home, away