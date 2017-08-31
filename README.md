# BayesBall
### version: 0.0.1 pre-alpha


Rational:
========

*BayesBall* is a small collection of Python modules for modelling the probabilistic events that occur in a typical game of baseball: events, for example, like pitching a baseball, catching a baseball, or stealing home from third base.


Every *BayesObject* is a subclass of [`ChainMap`](https://docs.python.org/3/library/collections.html#collections.ChainMap) with the maps shown below, ordered from last to first:

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

Every *BayesEvent* is a subclass of a *BayesObject*. What distinguishes a game *Event* from a game *Object* is that *Events* have prior probabilities defined over a finite set of *outcomes*.[^1] These *outcomes* and *prior probabilities* are, however, not meant to be directly accessible to the developer. Ideally, they would be created, and manipulated, by the internal logic of the *BayesEvent* itself--relative to the event's current reference class and action type. In other words, prior probability values are determined by logic encapsulated within `BayesEvent` class methods. This is a feature, not a bug. However, at the moment, the underlying logic is is based on unrealistic-- and simple --symmetry assumptions.

Ideally, `BayesEvent` instances should behave semi-autonomously.

The average modeller should never manipulate these prior probabilities directly--but only indirectly, by manipulating the *context* of an event. That is, by altering its *reference class*: by changing its state, if possible, and its environment.

In contrast to more frequentist simulations.


Using *BayesGame*:
=================

*BayesGame* provides a framework with which to develop the features of a baseball game. Currently, however, not many features are implemented.

The follow is what is implemented:



Short Term Goals:
================

[ ] have a systematic way of choosing player attributes, like strength, speed, precision, accuracy, etc.

[ ] determine prior probabilities for pitch/hit outcomes based on player attributes

[ ] add weather conditions

[ ] add game importance conditions, e.g., must win to reach playoffs, wildcard, etc.

[ ] pass the Ball class instance, with spin, velocity, etc.

[x] initialize lead-offs

[x] write player lead-off decision

[x] loop to see if players on base will steal

[x] write player steal decision

[x] write player steal T/F attribute `BaseBallPlayer.stealing`

[x] write pitcher decision to pick-off

[x] Pitcher's pickoff location (e.g. 'first')

[ ] MUST DO: check for runner collisions.

[ ] MUST DO: timing system ...

[x] need to see if a fielder can throw out bunt hit

[ ] make the solution a bit more realistic
	
[x] check to see if a runner is
        trying to steal, and throw.
		
[x] check with the catcher to see
        if a throw should be make, and,
        if so, check which base the
        catcher should throw to.
		
[ ] third strike, catcher drops ball, batter isnt' out...

[ ] give base stealers a benefit for stealing

[ ] force runners to go back if the ball is caught!




Long Term Goals:
===============

[ ] write a proper pitch/hit physics based on a physical possibility space, over which an outcome space can be defined. Then define a probability space over this outcome space. 

[ ] write a `BaseBallGame.manage` method to do things like swapping and substituting players, or more complicated actions, like infield shift, and other strategies dealing with pitcher substitutions, defensive substitutions, resting pitchers, pinch hitters/runners, and so on.

[ ] modify player.py so that a *BaseBallPlayer* has the following methods:
    
- A utility function to measure the success of player performance based on a player agent's decisions, like whether to throw a strike or curveball, or whether to swing for power or contact. One way to define such a function would be to first define the following methods:
- A utility function measuring the desirability between two gamestates. 
- An expected utility function measuring the expected desirability between two possible outcomes of an action.
- A method that ranks possible actions based on their expected desirability, *relative* to the current game state and environment. E.g. if the big HR-hitter is coming up to bat, and the score is tied in the ninth with two outs and two runners on bases, should the pitch walk or pitch to the hitter?

[ ] Store past stats, including past stats relative to batters/pitchers/teams played.

[ ] Create a separate library for modifying the prior probabilities of a  *BayesBall* game instance (including *BayesBall* players) so that simulations using this instance more closely predict, on average, the observed relative frequencies from historical baseball data. 

[^1]:  Some *Events*, like the *ShiftEvent* are to be used by a developer, or some other agent, like swapping players in a lineup, or are used internally in the game logic, like recording an out. These are deterministic events -- but because deterministic events are just probabilistic events defined over the possible probability values \{0,1\}, they are still strictly *BayesEvents*.
