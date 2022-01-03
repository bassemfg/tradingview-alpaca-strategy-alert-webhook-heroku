import dropbox
import datetime

try:
        
    dbx = dropbox.Dropbox('AVaJ5DdO1tMAAAAAAAAAAfTgfgz0TGEreE0ksmCN16cYjM8K-6LnhSTd7u48fa2K',
                          app_key='58cu3xkuq66z0w2', app_secret='j7lqripeqvesc27')
    filename = r'/herokusync/NQ1H_KNN.csv'
    f, r = dbx.files_download(filename)
    data = str(r.content, encoding='utf-8')
    
    #with open('/herokusync'+filename, "rb") as f:
    #    data = str(f.read())
    data+= str(datetime.datetime.now()) + ',,,' + "\r\n"
    dbx.files_upload(bytes(data, encoding='utf-8'), filename, mute=True, mode=dropbox.files.WriteMode.overwrite)
except Exception as e:
    print(e)
    