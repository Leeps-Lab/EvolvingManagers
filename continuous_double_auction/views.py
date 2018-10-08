# -*- coding: utf-8 -*-
from __future__ import division
from ._builtin import Page, WaitPage
from .models import Constants


def vars_for_all_templates(self):
    return {}


class Instructions(Page):

    def is_displayed(self):
        return self.round_number == 1


class MarketWaitPage(WaitPage):
    body_text = 'Waiting for all players to be ready'


class Market(Page):

    def vars_for_template(self):
        return {}


class Results(Page):

    def vars_for_template(self):
        self.player.set_payoff()
        return {}


page_sequence = [
        Instructions,
        MarketWaitPage,
        Market,
        Results
    ]
