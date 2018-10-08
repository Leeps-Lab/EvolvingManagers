from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)

from otree_redwood.models import DecisionGroup

author = 'Your name here'

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'evolving_managers'
    players_per_group = 2 
    num_rounds = 1


class Subsession(BaseSubsession):
    pass


class Group(DecisionGroup):

    def num_subperiods(self):
        return None

'''
class Group(RedwoodGroup):

    def _on_orders_event(self, event):
        if not self.bid_queue:
            self.bid_queue = []
        if not self.ask_queue:
            self.ask_queue = []
    
        player = self.get_player(event.participant.code)
        role = player.role()

        bid_queue_changed = False
        ask_queue_changed = False

        if event.value['type'] == 'bid':
            if role != 'buyer':
                return
            if event.value['price'] > player.currency:
                return

        bid_queue_changed |= self.remove_bid(buyer=player)

        if bid_queue_changed:
            self.send('bid_queue', self.bid_queue)
        if ask_queue_changed:
            self.send('ask_queue', self.ask_queue)

'''

class Player(BasePlayer):
    
    def initial_decision(self):
    	return 0

    def other_decision(self, initial_decision):
        return initial_decision

