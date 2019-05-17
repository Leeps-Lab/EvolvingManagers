from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants

from datetime import timedelta
from otree_redwood.models import DecisionGroup

class Instructions(Page):

    def is_displayed(self):
        return self.round_number == 1
    
    def vars_for_template(self):
        return {
            'instructions_link': self.session.config['instructions_link'],
        }

class DecisionWaitPage(WaitPage):

    def is_displayed(self):
        return self.round_number == 1
        # return self.round_number <= self.group.num_rounds()

class Decision(Page):

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()

class ResultsWaitPage(WaitPage):

    def after_all_players_arrive(self):
        for player in self.group.get_players():
            player.set_payoff()

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()

class Results(Page):

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()

def get_output_table_header(groups):
    return [
        'session_code',
        'round_number',
        'id_in_subsession',
        'tick',
        'p1_strategy',
        'p2_strategy',
        'p1_code',
        'p2_code',
        ]

def get_output_table(events):
    if not events:
        return []
    rows = []
    minT = min(e.timestamp for e in events if e.channel == 'state')
    maxT = max(e.timestamp for e in events if e.channel == 'state')
    p1, p2 = events[0].group.get_players()
    p1_code = p1.participant.code
    p2_code = p2.participant.code
    group = events[0].group
    # sets sampling frequency for continuous time output
    ticks_per_second = 2
    p1_decision = float('nan')
    p2_decision = float('nan')
    for tick in range((maxT - minT).seconds * ticks_per_second):
        currT = minT + timedelta(seconds=(tick / ticks_per_second))
        cur_decision_event = None
        while events[0].timestamp <= currT:
            e = events.pop(0)
            if e.channel == 'group_decisions':
                cur_decision_event = e
        if cur_decision_event:
            p1_decision = cur_decision_event.value[p1_code]
            p2_decision = cur_decision_event.value[p2_code]
        rows.append([
            group.session.code,
            group.round_number,
            group.id_in_subsession,
            tick,
            p1_decision,
            p2_decision,
            p1_code,
            p2_code,
        ])
    return rows

page_sequence = [
    DecisionWaitPage,
    Decision,
    ResultsWaitPage,
]
