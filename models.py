from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import csv, random, math


from otree_redwood.models import DecisionGroup, Event
from django.contrib.contenttypes.models import ContentType

author = 'Your name here'

doc = """
Your app description
"""

#Adding constants inputted from config .csv file
def parse_config(config_file):
    with open('evolving_managers/configs/' + config_file) as f:
        rows = list(csv.DictReader(f))

    rounds = []
    for row in rows:
        rounds.append({
            'period_length': int(row['period_length']),
            'evolve': float(row['evolve']),
            'c': float(row['c']),
        })
    return rounds

class Constants(BaseConstants):
    name_in_url = 'evolving_managers'
    players_per_group = None
    num_rounds = 100


class Subsession(BaseSubsession):
    def evolve(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['evolve']
    def c(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['c']
    # add any other constant vars per round here


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
        return  len(parse_config(self.session.config['config_file']))
    
    def period_length(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['period_length']
    
    def mean_matching(self):
        return True

class Player(BasePlayer):

    def initial_decision(self):
    	return .66

    def other_decision(self, initial_decision):
        return initial_decision
    
    def evolve_var(self):
        return self.participant.vars["evolve"] if "evolve" in self.participant.vars else 1

    def a_var(self):
        pass

    def set_payoff(self):
        decisions = list(Event.objects.filter(
                channel='group_decisions',
                content_type=ContentType.objects.get_for_model(self.group),
                group_pk=self.group.pk).order_by("timestamp"))

        try:
            period_start = Event.objects.get(
                    channel='state',
                    content_type=ContentType.objects.get_for_model(self.group),
                    group_pk=self.group.pk,
                    value='period_start')
            period_end = Event.objects.get(
                    channel='state',
                    content_type=ContentType.objects.get_for_model(self.group),
                    group_pk=self.group.pk,
                    value='period_end')
        except Event.DoesNotExist:
            return float('nan')

        self.payoff = self.get_payoff(period_start, period_end, decisions)

    def get_payoff(self, period_start, period_end, decisions):
        period_duration = period_end.timestamp - period_start.timestamp

        payoff = 0

        q1, q2 = 0.5, 0.5
        for i, d in enumerate(decisions):
            if not d.value: continue
            myDecision = d.value[self.participant.code]
            scalar = self.subsession.c()
            avg = sum(d.value.values()) / len(d.value)

            flow_payoff = (scalar * (myDecision * (1 - myDecision - avg)));
            print("flowPay")
            print(flow_payoff)


            if i + 1 < len(decisions):
                next_change_time = decisions[i + 1].timestamp
            else:
                next_change_time = period_end.timestamp
            decision_length = (next_change_time - d.timestamp).total_seconds()
            print("decisionlength")
            print(decision_length)
            payoff += decision_length * flow_payoff
            print("payoff")
            print(payoff)
            print("perioddurationSEC")
            print(period_duration.total_seconds)
        return payoff*100 / period_duration.total_seconds()



# add all vars here from bimatrix all Constants 
