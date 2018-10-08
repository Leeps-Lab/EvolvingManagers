# -*- coding: utf-8 -*-
from __future__ import division
from ._builtin import Page, WaitPage
from .models import Constants, parse_config
import copy

def vars_for_all_templates(self):
    return {
        "payoff_matrix": parse_config(self.session.config['config_file'])[self.round_number-1]['payoff_matrix'],
        "probability_matrix": parse_config(self.session.config['config_file'])[self.round_number-1]['probability_matrix'],
    }


class Introduction(Page):
    timeout_seconds = 100

    def is_displayed(self):
        return self.round_number == 1


class DecisionWaitPage(WaitPage):
    body_text = 'Waiting for all players to be ready'

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()


class Decision(Page):

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()

    def vars_for_template(self):
        displayed_subperiods = parse_config(self.session.config['config_file'])[self.round_number-1]['displayed_subperiods'],
        if displayed_subperiods == 0:
            displayed_subperiods = parse_config(self.session.config['config_file'])[self.round_number-1]['displayed_subperiods'],
        return {
            'displayed_subperiods': displayed_subperiods
        }


class Results(Page):

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()

    def vars_for_template(self):
        self.player.set_payoff()
        return {}

def get_config_columns(group):
    config = parse_config(group.session.config['config_file'])
    subperiod_length = config[group.round_number - 1]['subperiod_length']
    seconds_per_tick = config[group.round_number - 1]['seconds_per_tick']
    rest_length = config[group.round_number - 1]['rest_length']
    payoff_matrix = config[group.round_number - 1]['payoff_matrix']
    probability_matrix = config[group.round_number - 1]['probability_matrix']

    return [subperiod_length, seconds_per_tick, rest_length, payoff_matrix, probability_matrix]

def get_output_table_header():
    return [
        'timestamp_of_start',
        'session_ID',
        'period_id',
        'pair_id',     
        'p1_code',
        'p2_code',
        'p1_action',
        'p2_action',
        'p1_countGood',
        'p2_countGood',
        'p1_periodResult',
        'p2_periodResult',
        'p1_avg_payoffs',
        'p2_avg_payoffs',
        'num_subperiods',
        'subperiod_length',
        'seconds_per_tick',
        'rest_length',
        'payoff_matrix(AGood, ABad, BGood, BBad)',
        'probability_matrix(AA, AB, BA, BB)'
    ]

def get_output_table(events):
    if not events:
        return []
    rows = []
    p1, p2 = events[0].group.get_players()
    p1_code = p1.participant.code
    p2_code = p2.participant.code
    group = events[0].group
    config_columns = get_config_columns(group)
    for event in events:
        if event.channel == 'tick' and 'pauseProgress' in event.value and event.value['pauseProgress'] == event.value['printTime']:
            rows.append([
                event.timestamp,
                group.session.code,
                group.subsession_id,
                group.id_in_subsession,
                p1_code,
                p2_code,
                event.value['fixedDecisions'][p1_code],
                event.value['fixedDecisions'][p2_code],
                event.value['countGood'][p1_code],
                event.value['countGood'][p2_code],
                event.value['periodResult'][p1_code],
                event.value['periodResult'][p2_code],
                event.value['totalPayoffs'][p1_code]/parse_config(group.session.config['config_file'])[group.round_number-1]['subperiod_length'],
                event.value['totalPayoffs'][p2_code]/parse_config(group.session.config['config_file'])[group.round_number-1]['subperiod_length'],
                event.value['numSubperiods']
            ] + config_columns)

    rows.append("")
            
    return rows

page_sequence = [
        Introduction,
        DecisionWaitPage,
        Decision,
        Results
    ]
