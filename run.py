import datetime as dt
import os
import time

import pandas as pd
from sh import cd, git
import update
import plot

with open('regions.txt', 'r') as f:
    REGIONS = eval(f.read())

url = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv'
yesterday = pd.read_csv(url)
time.sleep(3)

while True:
    now = pd.read_csv(url)

    if now.equals(yesterday) is True:
        #update.update_and_save()
        #plot.plot()

        now = dt.datetime.now().strftime('%M:%H %Y-%m-%d')
        print(f'Updating at {now}')
        git('add', '.')
        today = dt.datetime.now().strftime('%Y-%m-%d')
        git('commit', '-m', f'{today}')
        git('push')
        break

    print('Waiting')
    time.sleep(600)
