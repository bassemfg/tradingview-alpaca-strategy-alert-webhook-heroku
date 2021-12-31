import os
is_prod = os.environ.get('IS_HEROKU', None)

if is_prod:
    API_KEY = os.environ.get('API_KEY')
    API_SECRET = os.environ.get('API_SECRET')

    WEBHOOK_PASSPHRASE =  os.environ.get('WEBHOOK_PASSPHRASE')
    DISCORD_WEBHOOK_URL = False # use a string containing your discord webhook url to enable
else:
    API_KEY = os.environ.get('API_KEY')
    API_SECRET = os.environ.get('API_SECRET')

    WEBHOOK_PASSPHRASE =  os.environ.get('WEBHOOK_PASSPHRASE')
    DISCORD_WEBHOOK_URL = False # use a string containing your discord webhook url to enable