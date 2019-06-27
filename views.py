from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants

from datetime import timedelta
from otree_redwood.models import DecisionGroup

class DecisionWaitPage(WaitPage):

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()

class Decision(Page):

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()

class ResultsWaitPage(WaitPage):

    def after_all_players_arrive(self):
        self.group.update_last_subperiod_payoffs()
        for player in self.group.get_players():
            player.set_payoff()

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()

class Results(Page):

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()

def get_output_table_header(groups):
    max_num_players = max(len(g.get_players()) for g in groups)
    header = [
        'session_code',
        'round_number',
        'id_in_subsession',
        'tick',
    ]
    for i in range(1, max_num_players+1):
        header.append('p{}_code'.format(i))
        header.append('p{}_strategy'.format(i))
        header.append('p{}_a_var'.format(i))
    return header

def get_output_table(events):
    if not events:
        return []
    rows = []
    minT = min(e.timestamp for e in events if e.channel == 'state')
    maxT = max(e.timestamp for e in events if e.channel == 'state')
    group = events[0].group
    players = group.get_players()
    # sets sampling frequency for continuous time output
    ticks_per_second = 2
    cur_decisions = {p.participant.code: float('nan') for p in players}
    cur_subp_vars = {p.participant.code: {'a_var': float('nan')} for p in players}
    for tick in range((maxT - minT).seconds * ticks_per_second):
        currT = minT + timedelta(seconds=(tick / ticks_per_second))
        while events[0].timestamp <= currT:
            e = events.pop(0)
            if e.channel == 'group_decisions':
                cur_decisions.update(e.value)
            elif e.channel == 'subperiod_start':
                cur_subp_vars.update(e.value)
        row = [
            group.session.code,
            group.round_number,
            group.id_in_subsession,
            tick,
        ]
        for p in players:
            pcode = p.participant.code
            row.append(pcode)
            row.append(cur_decisions[pcode])
            row.append(cur_subp_vars[pcode]['a_var'])
        rows.append(row)
    return rows

page_sequence = [
    DecisionWaitPage,
    Decision,
    ResultsWaitPage,
    Results,
]
