from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import csv, random, math
from datetime import timedelta

from jsonfield import JSONField
from otree_redwood.models import DecisionGroup, Event
from otree_redwood.utils import DiscreteEventEmitter
from django.contrib.contenttypes.models import ContentType

def parse_config(config_file):
    with open('evolving_managers/configs/' + config_file) as f:
        rows = list(csv.DictReader(f))

    rounds = []
    for row in rows:
        rounds.append({
            'period_length': int(row['period_length']),
            'subperiod_length': float(row['subperiod_length']),
            'c_var': float(row['c_var']),
            'bubble_style': row['bubble_style'],
            'initial_decision': float(row['initial_decision']),
            'window_size': int(row['window_size']),
        })
    return rounds

# randomly choose something from elems,
# elements are weighted by weights
def weighted_choice(elems, weights):
    total = sum(weights)
    rand = random.uniform(0, total)
    cur_sum = 0
    for i, w in enumerate(weights):
        cur_sum += w
        if rand < cur_sum:
            return elems[i]
    # not sure this is necessary, but if rand ends up being equal to total
    # we'll end up here. in that case just return the last elem
    return elems[-1]


class Constants(BaseConstants):
    name_in_url = 'evolving_managers'
    players_per_group = None
    num_rounds = 100


class Subsession(BaseSubsession):

    def c_var(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['c_var']

    def bubble_style(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['bubble_style']


class Group(DecisionGroup):

    def num_rounds(self):
        return len(parse_config(self.session.config['config_file']))
    
    def period_length(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['period_length']

    def subperiod_length(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['subperiod_length']

    def window_size(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['window_size']

    def window_size(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['window_size']
    
    def mean_matching(self):
        return True

    def update_last_subperiod_payoffs(self):
        # get the most recent subperiod start event for this group
        subperiod_start = Event.objects.filter(
            channel='subperiod_start',
            content_type=ContentType.objects.get_for_model(self),
            group_pk=self.pk
            ).latest("timestamp")

        # the decision set that happened before, but closest to the start of the subperiod.
        # gives each player's decision at the start of the subperiod.
        # this is NOT a decision event, it's a dict like group decisions
        try:
            initial_decision = Event.objects.filter(
                channel='group_decisions',
                content_type=ContentType.objects.get_for_model(self),
                group_pk=self.pk,
                timestamp__lt=subperiod_start.timestamp
                ).latest('timestamp').value
        # if this set doesn't exist, just use each player's initial decision
        # for the round
        except Event.DoesNotExist:
            initial_decision = {p.participant.code: p.initial_decision() for p in self.get_players()}

        # get all the decisions for this group which happened after the last subperiod start
        decisions = list(Event.objects.filter(
            channel='group_decisions',
            content_type=ContentType.objects.get_for_model(self),
            group_pk=self.pk,
            timestamp__gte=subperiod_start.timestamp)
            .order_by('timestamp'))
        
        for player in self.get_players():
            pcode = player.participant.code
            payoff = player.add_last_subperiod_payoff(subperiod_start, decisions, initial_decision)

    # get a list of all the payoff windows for this group
    def get_payoff_windows(self, subperiod_num):
        return [p.get_payoff_window(subperiod_num) for p in self.get_players()]
    
    # get A for all players in some subperiod
    def get_a_vars(self, subperiod_num):
        return [p.a_var(subperiod_num) for p in self.get_players()]

    def when_all_players_ready(self):
        super().when_all_players_ready()

        emitter = DiscreteEventEmitter(
            self.subperiod_length(),
            self.period_length(),
            self,
            self.subperiod_start,
            True)
        emitter.start()
    
    def subperiod_start(self, subperiod_num, total_num_subperiods):
        self.refresh_from_db()
        if subperiod_num > 0:
            self.update_last_subperiod_payoffs()

        msg = {}

        for player in self.get_players():
            pcode = player.participant.code
            msg[pcode] = {
                'a_var': player.a_var(subperiod_num),
                'payoff_window': player.get_payoff_window(subperiod_num-1)
            } 

        self.send('subperiod_start', msg)

class Player(BasePlayer):
    # holds the history of this player's subperiod payoffs
    _subperiod_payoffs = JSONField()
    # same as above but for A variables
    _a_vars = JSONField()

    def initial_decision(self):
        return parse_config(self.session.config['config_file'])[self.round_number-1]['initial_decision']

    # get A for a player in some subperiod
    def a_var(self, subperiod_num):
        self.refresh_from_db()

        # if we've already calculated A for this subperiod
        if subperiod_num < len(self._a_vars):
            return self._a_vars[subperiod_num]
        # if this is the very first A being calculated
        if subperiod_num == 0:
            random_a = random.uniform(0.5, 2)
            self._a_vars = [ random_a ]
            self.save(update_fields=['_a_vars'])
            return random_a
        # if the A for the previous subperiod hasn't been calculated
        if subperiod_num > len(self._a_vars):
            raise ValueError("can't generate A for subperiod {}".format(subperiod_num))
        
        # calculate the probability of evolution
        payoff_window = self.get_payoff_window(subperiod_num-1)
        all_payoff_windows = self.group.get_payoff_windows(subperiod_num-1)
        poff_windows_sorted = sorted(all_payoff_windows, reverse=True)
        # payoff position is a num between 0 and 1
        # 0 for the best payoff in the prev round, 1 for the worst
        payoff_position = poff_windows_sorted.index(payoff_window) / (len(poff_windows_sorted) - 1)
        evolve_prob = payoff_position * 0.2

        # if evolution occurs, choose from A vars of players whose payoff windows were above average
        # weight this choice by the distance from average
        if random.random() < evolve_prob:
            avg_payoff_window = sum(all_payoff_windows) / len(all_payoff_windows)
            prev_a_vars = self.group.get_a_vars(subperiod_num-1)
            weights = [max(0, poff-avg_payoff_window) for poff in all_payoff_windows]

            new_a = weighted_choice(prev_a_vars, weights)
            # add some distortion to the randomly chosen A
            new_a += random.uniform(-0.1, 0.1)
        # otherwise just use your A from the last round
        else:
            new_a = self.a_var(subperiod_num-1)
        # just append new a to the end of the array
        # we've already established that this is the correct position for this A
        self._a_vars.append(new_a)
        
        self.save(update_fields=['_a_vars'])
        return new_a
        
    # calculate the payoff for a specific player given a set of decisions made in a subperiod
    def add_last_subperiod_payoff(self, subperiod_start, decisions, initial_decision):
        self.refresh_from_db()

        pcode = self.participant.code
        payoff = 0

        # if decisions exists, then initial decision holds until the first decision event in the array
        if decisions:
            initial_decision_length = (decisions[0].timestamp - subperiod_start.timestamp).total_seconds()
        # otherwise the initial decision lasts the whole subperiod
        else:
            initial_decision_length = self.group.subperiod_length()
        payoff += self.calc_weighted_payoff(subperiod_start, initial_decision, initial_decision_length)

        for i, d in enumerate(decisions[1:]):
            if not d.value:
                continue

            if i+1 < len(decisions):
                next_change_time = decisions[i+1].timestamp
            else:
                next_change_time = subperiod_start.timestamp + timedelta(seconds=self.subperiod_length())
            decision_length = (next_change_time - d.timestamp).total_seconds()

            payoff += self.calc_weighted_payoff(subperiod_start, d.value, decision_length)

        if not self._subperiod_payoffs:
            self._subperiod_payoffs = []
        self._subperiod_payoffs.append(payoff / self.group.subperiod_length())

        self.save(update_fields=['_subperiod_payoffs'])
    
    # calculate a single weighted payoff for some decision dict and decision length
    def calc_weighted_payoff(self, subperiod_start, decision, decision_length):
        pcode = self.participant.code

        my_decision = decision[pcode]
        scalar = self.subsession.c_var()
        avg = sum(decision[k] for k in decision if k != pcode) / (len(decision) - 1)

        flow_payoff = scalar * my_decision * (1 - my_decision - avg);

        if flow_payoff < 0:
            return 0

        return decision_length * flow_payoff
    
    # get the payoff window for a certain player and subperiod
    # this value is called w in the specs
    def get_payoff_window(self, subperiod_num):
        if subperiod_num < 0:
            return 0

        self.refresh_from_db()
        pcode = self.participant.code
        window_size = self.group.window_size()
        window_start = max(0, subperiod_num - window_size)
        payoffs = self._subperiod_payoffs[window_start:subperiod_num]
        return sum(payoffs)
    
    def set_payoff(self):
        self.refresh_from_db()
        self.payoff = sum(self._subperiod_payoffs)
        self.save()
