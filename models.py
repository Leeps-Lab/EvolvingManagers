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
            'c_var': float(row['c_var']),
            'bubble_style': row['bubble_style'],
            'initial_decision': float(row['initial_decision']),
            'window_size': int(row['window_size']),
        })
    return rounds


class Constants(BaseConstants):
    name_in_url = 'evolving_managers'
    players_per_group = None
    num_rounds = 100


class Subsession(BaseSubsession):

    def c_var(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['c_var']

    def bubble_style(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['bubble_style']

    def window_size(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['window_size']


class Group(DecisionGroup):

    def num_subperiods(self):
        return None

    def num_rounds(self):
        return  len(parse_config(self.session.config['config_file']))
    
    def period_length(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['period_length']
    
    def mean_matching(self):
        return True

    def max_previous_payoff(self):
        return max(p.get_payoff_window() for p in self.get_players())


class Player(BasePlayer):

    _a_var = models.FloatField(null=True)

    def a_var(self):
        self.refresh_from_db()
        if self._a_var:
            return self._a_var

        if self.round_number == 1:
            self._a_var = random.uniform(0, 2)
        else:
            last_player = self.in_round(self.round_number - 1)
            last_payoff = last_player.get_payoff_window()
            previous_payoffs = [p.get_payoff_window() for p in last_player.group.get_players()]
            previous_payoffs.sort(reverse=True)
            # payoff_position = 0 if you got best payoff in last round, 1 if you got worst
            payoff_position = previous_payoffs.index(last_payoff) / (len(previous_payoffs) - 1)
            evolve_prob = payoff_position * 0.2
            last_a = last_player.a_var()
            if random.random() < evolve_prob:
                self._a_var = last_a + random.uniform(-0.1, 0.1)
            else:
                self._a_var = last_a
        
        self.save(update_fields=['_a_var'])
        return self._a_var

    def initial_decision(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['initial_decision']

    def get_payoff_window(self):
        width = self.subsession.window_size()
        players = self.in_rounds(max(self.round_number-width, 1), self.round_number)
        return sum(p.payoff for p in players)

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

        q1 = self.initial_decision()
        q2 = self.initial_decision()
        for i, d in enumerate(decisions):
            print(i, d)
            if (not d.value or
                d.timestamp < period_start.timestamp or
                d.timestamp > period_end.timestamp):
                continue

            myDecision = d.value[self.participant.code]
            scalar = self.subsession.c_var()
            avg = sum(d.value[k] for k in d.value if k != self.participant.code) / (len(d.value) - 1)

            flow_payoff = (scalar * (myDecision * (1 - myDecision - avg)));

            if flow_payoff < 0:
                continue

            if i+1 < len(decisions):
                next_change_time = decisions[i+1].timestamp
            else:
                next_change_time = period_end.timestamp
            decision_length = (next_change_time - d.timestamp).total_seconds()
            payoff += decision_length * flow_payoff

        return payoff*100 / period_duration.total_seconds()
