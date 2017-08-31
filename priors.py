
from context import outcomes, actions
from collections import namedtuple

def get_action_prior(action, default=True):
    fields = outcomes[actions.index(action)]
    return namedtuple('Prior', fields)
