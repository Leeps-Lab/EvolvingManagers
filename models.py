from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import csv, random, math


from otree_redwood.models import DecisionGroup

author = 'Your name here'

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'evolving_managers'
    players_per_group = 2 
    num_rounds = 100


class Subsession(BaseSubsession):
    pass


class Group(DecisionGroup):

    def when_all_players_ready(self):
        super().when_all_players_ready()

        if self.round_number == 1:
            for player in self.get_players():
                player.participant.vars["evolve"] = 1
        else:
            for player in self.get_players():
                last_group = player.in_round(self.round_number - 1).group
                last_decision = last_group.group_decisions[player.participant.code]
                player.participant.vars["evolve"] = 1

        self.save()

    def num_subperiods(self):
        return None

    def num_rounds(self):
        return 100 #change later to be a variable
    

    #Adding constants inputted from config .csv file
    def parse_config(config_file):
    with open('evolving_managers/configs/' + config_file) as f:
        rows = list(csv.DictReader(f))

    rounds = []
    for row in rows:
        rounds.append({
            'period_length': int(row['period_length']),
            'evolve': int(row['evolve']),
            'c': int(row['c']),
        })
    return rounds

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
    	return .66

    def other_decision(self, initial_decision):
        return initial_decision
    
    def evolve_var(self):
        return self.participant.vars["evolve"] if "evolve" in self.participant.vars else 1

# add all vars here from bimatrix all Constants 
