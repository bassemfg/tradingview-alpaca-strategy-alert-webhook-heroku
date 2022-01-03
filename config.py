import os
is_prod = os.environ.get('IS_HEROKU', None)

if is_prod:
    API_KEY = os.environ.get('API_KEY')
    API_SECRET = os.environ.get('API_SECRET')
    DB_App1_ACCESS_TOKEN = os.environ.get('db_app1_access_token')
    db_app_key = os.environ.get('db_app_key')
    db_app_secret = os.environ.get('db_app_secret')
    WEBHOOK_PASSPHRASE =  os.environ.get('WEBHOOK_PASSPHRASE')
    DISCORD_WEBHOOK_URL = False # use a string containing your discord webhook url to enable
else:
    API_KEY = os.environ.get('API_KEY')
    API_SECRET = os.environ.get('API_SECRET')
    DB_App1_ACCESS_TOKEN = os.environ.get('db_app1_access_token')
    db_app_key = os.environ.get('db_app_key')
    db_app_secret = os.environ.get('db_app_secret')
    WEBHOOK_PASSPHRASE =  os.environ.get('WEBHOOK_PASSPHRASE')
    DISCORD_WEBHOOK_URL = False # use a string containing your discord webhook url to enable
