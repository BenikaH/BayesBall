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
from collections import defaultdict, ChainMap, namedtuple
import logging

logging.basicConfig(level=logging.INFO)

__empty__ = '<missing>'

ReferenceClass = namedtuple('ReferenceClass', ['state','environment'])
Action = namedtuple('Action', ['action', 'subjects'])
Outcome = namedtuple('Outcome', ['result', 'record', 'details'])

class CoreBayesEvent(ChainMap):
    """CoreBayesEvent subclasses ChainMap, from Python base module,
    collections. Every event during the simulation is an instance
    of a ChainMap consisting of three dicts, or mappings.

    - The first mapping is an instance of the namedtuple ReferenceClass.

    - The second mapping is an instance of the namedtuple Action.

    - The third mapping, which is initially empty, is where the outcome
    of an an action is stored, relative to the context, the ReferenceClass.

    Paramaters:
    ----------
    1. action_class_context : dict

    The action dict must include the following fields:

    - 'action' : str
    - 'subjects' : list of subjects, like player objects.

    2. reference_class_context : dict

    The reference class dict must include the following fields:

    - 'state' : namedtuple
    - 'environment' : NotImplemented (See game.py for an implementation.) 
    """    
    def __init__(self, action_class_context, reference_class_context):
        assert isinstance(action_class_context, dict)
        assert isinstance(reference_class_context, dict)
        super().__init__(
            {'referenceclass': ReferenceClass(**reference_class_context)},
            {'action': Action(**action_class_context)},
            {'outcome': __empty__}
        )
class _BayesAction(CoreBayesEvent):
    """Template for Core Bayes Event"""
    def __init__(self, action_context, reference_context):
        self._happened = False
        super().__init__(action_context, reference_context)

    @property
    def action(self):
        """Returns the Action namedtuple for the current event."""
        return self.get('action')

    @property
    def outcome(self):
        """Returns the Outcome namedtuple for the current event."""
        return self.get('outcome')

    @property
    def ref_class(self):
        """Returns the ReferenceClass namedtuple
        for the current event.
        """
        return self.get('referenceclass')

    @property
    def result(self):
        """Returns the result of the Outcome
        namedtuple for the current event.
        """
        if isinstance(self.outcome, str):
            raise ValueError('Bad outcome "{}"!'.format(self.outcome))
        return self.outcome.result

    @property
    def record(self):
        """Returns the record of the Outcome
        namedtuple for the current event.
        """
        return self.outcome.record

    @property
    def details(self):
        """Returns the details of the Outcome
        namedtuple for the current event.
        """
        return self.outcome.details

    @property
    def happened(self):
        """Returns True if the event has already
        happened, and false otherwise.
        """
        return self._happened

    @property
    def name(self):
        """Returns a string, the name, of the current event."""
        return type(self).__name__

    def has_name(self, clsname):
        """Returns True if the current event's name is equal to the strong clsname

        Paramaters:
        ----------

        clsname : str
        """        
        assert isinstance(clsname, str)
        return clsname == self.name

    def _build_action_context(self, action, subjects):
        return dict([('action', action), ('subjects', subjects)])

    def _build_game_context(self, state=None, environment=None):
        return dict([('state', state), ('environment', environment)])

    def __repr__(self):
        return ('-bayes {} ({})\n--{}\n--A: <action: {}> <subjects: {}>\n'\
            + '--RC: <state: {}> <env: {}>\n').format(
            self.name,
            id(self),
            self.outcome,
            self.action.action,
            list(self.action.subjects._asdict().values()),
            self.ref_class.state, self.ref_class.environment
        )
    def __str__(self):
        return self.__repr__()

class BayesAction(_BayesAction):
    """Main Template for coding a bayes action.

    The developer MUST overload the following class methods:
    - upkeep
    - random_triggers
    - _perform_action

    The developer can also manually set self.debug as True or False,
    depending on whether they want to see debugging information. 
    """
    def __init__(self, action, ref_class, time=None, *subjects):
        self.start_time = time
        self.debug = False
        super().__init__(action, ref_class)

        if self.debug:
            logging.info('Entering event {}'.format(self.name))

        self.random_triggers() # I current don't take advantage of this
        self.upkeep()

    def upkeep(self): raise NotImplementedError
    def random_triggers(self): raise NotImplementedError
    def _perform_action(self): raise NotImplementedError

    @property
    def make_happen(self):
        """The main method for performing an event, the results of which
        are added to the current Outcome mapping of the current event.
        """
        if self.debug:
            logging.info('Current outcome: {}'.format(self.outcome))

        self._happened = True
        self._perform_action()

        if self.debug:
            logging.info('Exiting event {}'.format(self.name))

    def isaction(self, *classnames):
        """Returns True if all the classnames, which are strings
        as names of classes, are subclasses of the current class
        instance type (default: BayesAction).
        """
        subnames = list(cls.__name__ for cls in type(self).__subclasses__())
        return all(name in subnames for name in classnames)
