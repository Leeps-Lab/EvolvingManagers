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

    # def vars_for_template(self):
    #     return {
        
    #     }

class ResultsWaitPage(WaitPage):

    def after_all_players_arrive(self):
        pass


class Results(Page):

    def is_displayed(self):
        return self.round_number <= self.group.num_rounds()

page_sequence = [
    Decision,
    ResultsWaitPage,
    Results
]
