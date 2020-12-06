import pandas as pd
import datetime as dt
import time

import update
import plot

with open('regions.txt', 'r') as f:
    REGIONS = eval(f.read())

url = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv'
yesterday = pd.read_csv(url)
time.sleep(3)

while True:
    now = pd.read_csv(url)

    if now.equals(yesterday) is not True:
        update.update_and_save()
        plot.plot()

        os.system('cd ~/covid') # probably useless 
        os.system('git add .')
        os.system(f'git commit -m "{dt.datetime.now().strftime('%Y-%m-%d')}"')
        os.system('git push')
        break

    time.sleep(600)
