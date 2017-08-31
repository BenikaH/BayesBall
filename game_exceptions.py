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

"""Template class, to be used in later versions


Ideally, I would use these to model player injuries.

I might be best, however, to model player errors using
EventShift instead of as raising an exception.
"""

class GameException(Exception):
    def __init__(self, parent_event_name, event):
        super().__init__(message)
        self._event = event
        self._parent_event_name = parent_event_name
    @property
    def event(self): return self._event 
    @property
    def parent_name(self): return self._parent_event_name

class GameInjury(GameException):
    pass

class GameError(GameException):
    pass
