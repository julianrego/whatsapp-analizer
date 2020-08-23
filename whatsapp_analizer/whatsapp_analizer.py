import pandas as pd
import re
import matplotlib.pyplot as plt

class WhatsappAnalizer(object):
    
    __punctuation = '¿¡!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'

    def __init__(self, path_to_chat):
        self.path_to_chat = path_to_chat

        self.__df = self.parse_txt(self.path_to_chat)
        self.__messages_by_user = None
        self.__words_by_user = None #TODO: do it

    @property
    def df(self):
        return self.__df

    @property
    def users(self):
        return self.__users

    @property
    def messages_by_user(self):
        if self.__messages_by_user is None:
            self.messages_sent_by_user()
        return self.__messages_by_user

    @property
    def words_by_user(self):
        if self.__words_by_user is None:
            self.words_sent_by_user()
        return self.__words_by_user

    def parse_txt(self, path):

        with open(path) as f:
            data_txt = f.read()

        #Parseo bien ese txt con formato de mierda
        lista = re.compile('(\d{1,2}\/\d{1,2}\/\d{2}\s\d{2}:\d{2})\s-\s(?:\u200e*)').split(data_txt)
        
        df = pd.DataFrame(data={
            'timestamp':[lista[index] for index in range(len(lista)) if index%2==1],
            'temp':[lista[index] for index in range(len(lista)) if (not index%2==1 and index!=0)]
        })

        df['timestamp'] = pd.to_datetime(df['timestamp'] , format = '%d/%m/%y %H:%M')

        df[['user','message']] = df['temp'].str.split(':', 1, expand=True)
        df['message'] = df['message'].str.replace('\\n', ' ')
        df = df.drop(columns = 'temp')
        
        #si no hay usuario, es porque no fue un mensaje si no una accion. Lo pongo como tal
        df['action'] = df[df['message'].isna()]['user'].str.replace('\\n', ' ')
        df.loc[df.loc[:,'message'].isna(), 'user'] = None

        self.__users = df.user.dropna().unique()

        df.loc[df.loc[:,'message'].isna(), 'user'] = df['action'].apply(self.__which_user)

        #Saco signos de puntuacion y saco mayusculas
        df['message'] = df['message'].str.replace('[{}]'.format(self.__punctuation), '').str.lower().str.strip()

        df = df.set_index('timestamp')

        return df
    
    def __which_user(self, x):
        for user in self.__users:
            if isinstance(x, str) and x.startswith(user):
                return user
        return None

    def __count_words(self, group):
        words_quantity = group['message'].str.split(' ').apply(len).sum()
        return words_quantity

    def messages_sent_by_user(self):
        self.__messages_by_user = self.__df[self.__df['message'].notna()].groupby('user')['message'].count()
        return self.__messages_by_user

    def words_sent_by_user(self):
        self.__words_by_user = self.__df[self.__df['message'].notna()].groupby('user').apply(self.__count_words)
        return self.__words_by_user

    def plot_messages_by_day(self, **kwargs):
        """
        los kwargs se le pasan al metodo plot de pandas
        """

        self.__df.resample('1D')['message'].count().plot(title = 'Messages by day', **kwargs)

    def plot_messages_by_week(self, **kwargs):
        """
        los kwargs se le pasan al metodo plot de pandas
        """

        self.__df.resample('1W')['message'].count().plot(title= 'Messages by week', **kwargs)

    def plot_messages_by_month(self, **kwargs):
        """
        los kwargs se le pasan al metodo plot de pandas
        """

        self.__df.resample('1M')['message'].count().plot(title= 'Messages by month', **kwargs)

    def plot_messages_by_week_by_user(self,users = None, **kwargs):
        """
        los kwargs se le pasan al metodo plot de pandas
        """
        if users is None:
            users = list(self.__users)

        assert isinstance(users, (list, str)), 'users must by a string or a list'
        
        if isinstance(users, str):
            users = [users]

        assert all(user in self.__users for user in users), f'user/s {[user for user in users if user not in self.__users]}'

        
        
        for user in users:
            self.__df[self.__df['user']==user].resample('1W')['message'].count().plot(**kwargs, label = user)
        plt.legend()
