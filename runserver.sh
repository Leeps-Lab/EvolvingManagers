daphne -b 0.0.0.0 -p 8000 otree.asgi:channel_layer &
python manage.py runworker --only-channels=http.* --only-channels=otree.* &
python manage.py runworker --only-channels=http.* --only-channels=otree.* &
python manage.py runworker --only-channels=http.* --only-channels=otree.* &
python manage.py runworker --only-channels=http.* --only-channels=otree.* &
python manage.py runworker --only-channels=websocket.* &
python manage.py runworker --only-channels=websocket.* &
python manage.py runworker --only-channels=websocket.* &
python manage.py runworker --only-channels=websocket.* &
python manage.py runworker --only-channels=websocket.* &
python manage.py runworker --only-channels=websocket.* &
python manage.py runworker --only-channels=websocket.* &
python manage.py runworker --only-channels=websocket.*