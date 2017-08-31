# BayesBall

written by: Chris French

version: 0.1.0 Pre-Alpha

Rationale:
=========

*BayesBall* is a small collection of Python modules for modelling the probabilistic events that occur in a typical game of baseball. Events, for example, like pitching a baseball, catching a baseball, or stealing home.

Every *BayesObject* is a subclass of [`ChainMap`](https://docs.python.org/3/library/collections.html#collections.ChainMap) with the mappings shown below (ordered from last to first):

- map of the event's reference class:
    - `GameState` : `namedtuple`
    - `Environment` : `namedtuple`

- map of the current action:
    - action type : `str` 
    - action inputs, the `subjects` : `list`
  
- map of the *outcome*:
    - outcome result : `str`
    - outcome record : `str`
    - details about the `subjects` : `dict`

Every *BayesEvent* is a subclass of a *BayesObject*. What distinguishes a game *Event* from a game *Object* is that *Events* have prior probabilities defined over a finite set of *outcomes*.[1] 

These *outcomes* and *prior probabilities* are not intended to be directly changed by the developer. Instead, *outcomes* are initialized (relative to the event's current reference class and action type) and manipulated by the logic internal to the *BayesEvent* itself. 

In other words, prior probability values are fixed by the logic encapsulated within `BayesEvent` class methods. This is a feature, not a bug. 

Ideally, `BayesEvent` instances should behave semi-autonomously. The average modeller should never manipulate these prior probabilities directly--but only indirectly, by manipulating the *context* of an event. That is, by altering its *reference class*: by changing its state, if possible, and its environment.

Presently, however, the underlying logic in the main `BayesEvent`-- `PitchEvent` --is unrealistic: it relies too heavily on symmetry assumptions rather than the `Environment` and players in the current lineups.

*BayesBall* is different from baseball simulations which are frequentist in nature: whereas *BayesBall* fixes prior probabilities explicitly, other simulation engines define event probabilities in terms of relative frequencies.  For example, these simulations may calculate the probability that a hit pitch will result in a single by first assuming that, say, at most *N* (= 100,000) hits will occur over the course of a season. If *M* is the number of other hit events that could occur during an at-bat (excluding singles), the probability that an at-bat will result in a single, if a hit event must occur, is just 

(*N*-*n*) / (*N*+*M*)

where *n* is the number of singles that have happened in the season so far.

Using *BayesGame*:
=================

*BayesGame* provides a framework with which to develop the features of a baseball game. Currently, however, not many features are implemented.

Currently, the only dependencies are [NumPy](http://www.numpy.org/) and [SciPy](https://www.scipy.org/scipylib/index.html). 

To install these dependencies, use

`pip3 install numpy`

and

`pip3 install scipy`

and that's it. Aside from Python's [curses](https://docs.python.org/3/library/curses.html#module-curses) library, there are no other dependencies.

To play through a toy baseball game example, simply run:

`python3 game.py`

If you are using Mac/Linux, play through a game with a curses-based app:

`python3 app.py`


Short Term Goals:
================

- [ ] decide on a systematic way of choosing player attributes, like strength, speed, precision, accuracy, etc.

- [ ] determine prior probabilities for pitch/hit outcomes based on player attributes

- [ ] add weather conditions

- [ ] add game importance conditions, e.g., must win to reach playoffs, wildcard, etc.

- [ ] pass the Ball class instance, with spin, velocity, etc.

- [x] initialize lead-offs

- [x] write player lead-off decision

- [x] loop to see if players on base will steal

- [x] write player steal decision

- [x] write player steal T/F attribute `BaseBallPlayer.stealing`

- [x] write pitcher decision to pick-off

- [x] Pitcher's pickoff location (e.g. 'first')

- [ ] MUST DO: check for runner collisions.

- [ ] MUST DO: timing system ...

- [x] need to see if a fielder can throw out bunt hit

- [x] check to see if a runner is
        trying to steal, and throw.
		
- [x] check with the catcher to see
        if a throw should be make, and,
        if so, check which base the
        catcher should throw to.
		
- [ ] third strike, catcher drops ball, batter isnt' out...

- [ ] give base stealers a benefit for stealing

- [ ] force runners to go back if the ball is caught!

- [ ] catch success penalties for not good throw results


Long Term Goals:
===============

- [ ] write a proper pitch/hit physics based on a physical possibility space, over which an outcome space can be defined. Then define a probability space over this outcome space. 

- [ ] write a `BaseBallGame.manage` method to do things like swapping and substituting players, or more complicated actions, like infield shift, and other strategies dealing with pitcher substitutions, defensive substitutions, resting pitchers, pinch hitters/runners, and so on.

- [ ] modify player.py so that a *BaseBallPlayer* has the following methods:
    
- A utility function to measure the success of player performance based on a player agent's decisions, like whether to throw a strike or curveball, or whether to swing for power or contact. One way to define such a function would be to first define the following methods:
- A utility function measuring the desirability between two gamestates. 
- An expected utility function measuring the expected desirability between two possible outcomes of an action.
- A method that ranks possible actions based on their expected desirability, *relative* to the current game state and environment. E.g. if the big HR-hitter is coming up to bat, and the score is tied in the ninth with two outs and two runners on bases, should the pitch walk or pitch to the hitter?

- [ ] Store past stats, including past stats relative to batters/pitchers/teams played.

- [ ] Create a separate library for modifying the prior probabilities of a  *BayesBall* game instance (including *BayesBall* players) so that simulations using this instance more closely predict, on average, the observed relative frequencies from historical baseball data. 

[1]:  Some *Events*, like `ShiftEvent`, can be used to swap or sup players during a game. These are deterministic events -- but because deterministic events are just probabilistic events defined over the possible probability values \{0,1\} --they are still *BayesEvents*.

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
