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
