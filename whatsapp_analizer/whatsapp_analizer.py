import pandas as pd
import re

class WhatsappAnalizer(object):

    def __init__(self, path_to_chat):
        self.path_to_chat = path_to_chat

        self.df = self.parse_txt(self.path_to_chat)

    def parse_txt(self, path):

        with open(path) as f:
            data_txt = f.read()

        #Parseo bien ese txt con formato de mierda
        lista = re.compile('(\d{1,2}\/\d{1,2}\/\d{2}\s\d{2}:\d{2})\s-\s(?:\u200e*)').split(data_txt)
        
        df = pd.DataFrame(data={
            'timestamp':[lista[index] for index in range(len(lista)) if index%2==1],
            'temp':[lista[index] for index in range(len(lista)) if (not index%2==1 and index!=0)]
        })

        df[['user','message']] = df['temp'].str.split(':', 1, expand=True)
        df['message'] = df['message'].str.replace('\\n', ' ')
        df = df.drop(columns = 'temp')
        
        #si no hay usuario, es porque no fue un mensaje si no una accion. Lo pongo como tal
        df['action'] = df[df['message'].isna()]['user'].str.replace('\\n', ' ')
        df.loc[df.loc[:,'message'].isna(), 'user'] = None

        self.users = df.user.dropna().unique()

        df.loc[df.loc[:,'message'].isna(), 'user'] = df['action'].apply(self.__which_user)

        return df
    
    def __which_user(self, x):
        for user in self.users:
            if isinstance(x, str) and x.startswith(user):
                return user
        return None