import pandas as pd
import re
import matplotlib.pyplot as plt

class WhatsappAnalizer(object):
    
    __punctuation = '¿¡!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'

    def __init__(self, path_to_chat):
        self.path_to_chat = path_to_chat

        self.__df = self.parse_txt(self.path_to_chat)
        self.__messages_by_user = None
        self.__words_by_user = None 
        self.__messages_by_day = None
        self.__messages_by_week = None
        self.__messages_by_month = None
        self.__messages_by_week_by_user = None

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

    @property
    def messages_by_day(self):
        if self.__messages_by_day is None:
            self.get_messages_by_day()
        return self.__messages_by_day

    @property
    def messages_by_week_by_user(self):
        if self.__messages_by_week_by_user is None:
            self.get_messages_by_week_by_user()
        return self.__messages_by_week_by_user

    def parse_txt(self, path):
        """
        Parsea el txt con los mensajes de whatsapp. 
        -path: path con el archivo
        """
        with open(path) as f:
            data_txt = f.read()

        #Parseo bien ese txt con formato de mierda
        pattern = re.compile('(\d{1,2}\/\d{1,2}\/\d{2}\s\d{2}:\d{2})\s-\s(?:\u200e*)')
        lista = pattern.split(data_txt)
        
        df = pd.DataFrame(data={
            'timestamp':[lista[index] for index in range(len(lista)) if index%2==1],
            'temp':[lista[index] for index in range(len(lista)) if (not index%2==1 and index!=0)]
        })

        df['timestamp'] = pd.to_datetime(df['timestamp'] , format='%d/%m/%y %H:%M')

        df[['user','message']] = df['temp'].str.split(':', 1, expand=True)
        df['message'] = df['message'].str.replace('\\n', ' ')
        df = df.drop(columns = 'temp')
        
        #si no hay mensaje, es porque no fue un mensaje si no una accion. Lo pongo como tal
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
        """
        Cuantos mensajes mando cada usuario?
        """
        self.__messages_by_user = self.__df[self.__df['message'].notna()].groupby('user')['message'].count()
        return self.__messages_by_user

    def words_sent_by_user(self):
        """
        Cuantas palabras escribio cada usuario?
        """
        self.__words_by_user = self.__df[self.__df['message'].notna()].groupby('user').apply(self.__count_words)
        return self.__words_by_user

    def get_messages_by_day(self):
        self.__messages_by_day = self.__df.resample('1D')['message'].count()
        return self.__messages_by_day
    
    def plot_messages_by_day(self, **kwargs):
        """
        los kwargs se le pasan al metodo plot de pandas
        """
        assert not (self.__messages_by_day is None), 'First call get_messages_by_day'
        self.__messages_by_day.plot(title = 'Messages by day', **kwargs)

    def get_messages_by_week(self):
        self.__messages_by_week = self.__df.resample('1W')['message'].count()
        return self.__messages_by_week
    
    def plot_messages_by_week(self, **kwargs):
        """
        los kwargs se le pasan al metodo plot de pandas
        """
        assert not (self.__messages_by_week is None), 'First call get_messages_by_week'
        self.__df.resample('1W')['message'].count().plot(title= 'Messages by week', **kwargs)

    def get_messages_by_month(self):
        self.__messages_by_month = self.__df.resample('1M')['message'].count()
        return self.__messages_by_month
    
    def plot_messages_by_month(self, **kwargs):
        """
        los kwargs se le pasan al metodo plot de pandas
        """
        assert not (self.__messages_by_month is None), 'First call get_messages_by_month'
        self.__messages_by_month.plot(title= 'Messages by month', **kwargs)

    def get_messages_by_week_by_user(self):

        messages_by_week_by_user = {}

        for user in self.__users:
            messages_by_week_by_user[user] = self.__df[self.__df['user']==user].resample('1W')['message'].count()
        self.__messages_by_week_by_user = messages_by_week_by_user
        return self.__messages_by_week_by_user

    def plot_messages_by_week_by_user(self,users=None, **kwargs):
        """
        los kwargs se le pasan al metodo plot de pandas
        users tiene que ser uno de los usuarios del grupo, o una lista con algun subset de ellos
        por default los grafica todos 
        """

        assert not (self.__messages_by_week_by_user is None), 'First call get_messages_by_week_by_user'

        if users is None:
            users = list(self.__users)

        assert isinstance(users, (list, str)), 'users must by a string or a list'
        
        if isinstance(users, str):
            users = [users]

        assert all(user in self.__users for user in users), \
                 f'user/s {[user for user in users if user not in self.__users]} are not in the data'

        for user in users:
            self.__messages_by_week_by_user[user].plot(label = user, **kwargs)
        plt.title('Messages by user by week')
        plt.legend()


if __name__ == '__main__':
    import argparse
    import os

    description='Graficos con metricas de grupo de Whatsapp. ' +\
        'Cantidad de mensajes y palabras en total, y por usuario'

    parser = argparse.ArgumentParser(
        prog='Whatsapp Analizer',
        description=description
    )

    parser.add_argument('path', type=str, help='path de .txt que tiene la conversacion')
    parser.add_argument('--path_to_save', type=str, help='Directory to save plots')

    args = parser.parse_args()

    #where to save the results
    if not args.path_to_save:
        path_to_save = os.getcwd()
    else:
        path_to_save = args.path_to_save

    chat_name = args.path.split(os.sep)[-1].replace('.txt', '')
    path_to_save = os.path.join(path_to_save, 'Analisis de ' + chat_name)
    os.mkdir(path_to_save)

    #analize chat
    analizer = WhatsappAnalizer(args.path)

    ###GRAFICOS GENERALES###
    #TODO: cuando haga mejor lo de palabras por periodo, y lo haga para cada usuario
    # separar los directorios de los distintos resultados

    #mensajes por usuario
    analizer.messages_by_user.plot(kind='bar', title = 'Mensajes por usuario')
    plt.tight_layout()
    plt.savefig(os.path.join(path_to_save, 'messages_by_user.jpg'))
    plt.close()

    #palabras por usuario
    analizer.words_by_user.plot(kind='bar', title='Palabras por usuario')
    plt.tight_layout()
    plt.savefig(os.path.join(path_to_save, 'words_by_user.jpg'))
    plt.close()

    #palabras promedio por mensaje
    (analizer.words_by_user/analizer.messages_by_user).plot(kind='bar', title='Palabras promedio por mensaje')
    plt.tight_layout()
    plt.savefig(os.path.join(path_to_save, 'average_words_by_user.jpg'))
    plt.close()

    #mensajes por dia
    analizer.get_messages_by_day()
    analizer.plot_messages_by_day()
    plt.tight_layout()
    plt.savefig(os.path.join(path_to_save, 'messages_by_day.jpg'))
    plt.close()

    #mensajes por semana
    analizer.get_messages_by_week()
    analizer.plot_messages_by_week()
    plt.tight_layout()
    plt.savefig(os.path.join(path_to_save, 'messages_by_week.jpg'))
    plt.close()

    #mensajes por mes
    analizer.get_messages_by_month()
    analizer.plot_messages_by_month()
    plt.tight_layout()
    plt.savefig(os.path.join(path_to_save, 'messages_by_month.jpg'))
    plt.close()

    #mensajes por semana por usuario
    analizer.get_messages_by_week_by_user()
    analizer.plot_messages_by_week_by_user()
    plt.tight_layout()
    plt.savefig(os.path.join(path_to_save, 'messages_by_week_by_user.jpg'))
    plt.close()

    ###RESULTADOS POR USUARIO###

    by_user = os.path.join(path_to_save, 'users')
    os.mkdir(by_user)

    for user in analizer.users:
        analizer.plot_messages_by_week_by_user(users = user)
        plt.tight_layout()
        plt.savefig(os.path.join(by_user, f'{user}.jpg'))
        plt.close()


    print(os.getcwd())