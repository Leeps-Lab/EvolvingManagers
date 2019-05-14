sample session config:
```
{
    'name': 'evolving_managers',
    'display_name': 'Evolving Managers',
    'num_demo_participants': 2,
    'app_sequence': ['evolving_managers', 'payment_info'],
    'config_file': 'demo.csv',
},
```

the 'bubble_style' field in config determines how the other players' bubble is drawn. if it's set to 'none', no bubble is drawn. if it's set to 'strategy', the bubble is drawn on the x axis. if it's set to 'payoff', its height shows the other players' average payoff.