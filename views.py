from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants

from otree_redwood.models import DecisionGroup

class Instructions(Page):

    def is_displayed(self):
        return self.round_number == 1
    
    def vars_for_template(self):
        return {
            'instructions_link': self.session.config['instructions_link'],
        }

class Decision(Page):

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()

class ResultsWaitPage(WaitPage):

    def after_all_players_arrive(self):
        pass

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()

class Results(Page):

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()

    def get_output_table_header():
    return [
        'session_code',
        'subsession_id',
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
        config_columns = get_config_columns(group)
        # sets sampling frequency for continuous time output
        ticks_per_second = 2
        p1_decision = float('nan')
        p2_decision = float('nan')
        p1_target = float('nan')
        p2_target = float('nan')
        for tick in range((maxT - minT).seconds * ticks_per_second):
            currT = minT + timedelta(seconds=(tick / ticks_per_second))
            cur_decision_event = None
            while events[0].timestamp <= currT:
                e = events.pop(0)
                if e.channel == 'group_decisions':
                    cur_decision_event = e
                    if e.participant.code == p1_code:
                        p1_target = e.value
                    else:
                        p2_target = e.value
            if cur_decision_event:
                p1_decision = cur_decision_event.value[p1_code]
                p2_decision = cur_decision_event.value[p2_code]
            rows.append([
                group.session.code,
                group.subsession_id,
                group.id_in_subsession,
                tick,
                p1_decision,
                p2_decision,
                p1_code,
                p2_code,
            ] + config_columns)
        return rows

page_sequence = [
    Decision,
    ResultsWaitPage,
    Results
]
