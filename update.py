import datetime as dt
import numpy    as np
import pandas   as pd

import time

with open('regions.txt', 'r') as f:
	REGIONS = eval(f.read())

def update():
	url = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/'

	urlIt = url+'dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv'
	italia = pd.read_csv(urlIt)

	time.sleep(1)

	urlReg = url+'dati-regioni/dpc-covid19-ita-regioni.csv'
	regioni = pd.read_csv(urlReg)

	return italia, regioni

def process(df, region):

	if region != 'Italia':
		df = df[df.denominazione_regione == region].copy()

	to_datetime = lambda x: dt.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")
	df['data'] = df.data.map(to_datetime)
    
	df.sort_values('data', inplace=True)
	df = df[df.data > dt.datetime(2020, 9, 30)].reset_index()

	df['netto_positivi'] = df.variazione_totale_positivi.copy()
	df['positivi'] = df.nuovi_positivi.copy()
	df['delta_positivi'] = np.sqrt(df.positivi)

	df['sintomi'] = df.ricoverati_con_sintomi - df.ricoverati_con_sintomi.shift(1,fill_value=0)
	df['sintomi'] = df.sintomi.map(int)

	df['intensiva'] = df.terapia_intensiva - df.terapia_intensiva.shift(1,fill_value=0)
	df['intensiva'] = df.intensiva.map(int)

	df['guariti'] = df.dimessi_guariti - df.dimessi_guariti.shift(1,fill_value=0)
	df['guariti'] = df.guariti.map(int)

	df['morti'] = df.deceduti - df.deceduti.shift(1,fill_value=0)
	df['morti'] = df.morti.map(int)

	diagnostico = df.casi_da_sospetto_diagnostico - df.casi_da_sospetto_diagnostico.shift(1,fill_value=0)
	df['diagnostico'] = diagnostico.fillna(method='ffill').fillna(0).map(int)

	df['screening'] = df.casi_da_screening - df.casi_da_screening.shift(1,fill_value=0)
	df['screening'] = df.screening.fillna(method='ffill').fillna(0).map(int)

	df['tamponi'] = df.tamponi - df.tamponi.shift(1, fill_value=0)
	df['tamponi'] = df.tamponi.map(int)

	df = df.drop([0]).reset_index()
	df = df[['data', 'totale_casi', 'positivi', 'netto_positivi', 'tamponi', 'guariti', 'totale_positivi',
             'morti', 'sintomi', 'intensiva', 'diagnostico', 'screening', 'delta_positivi']].copy()
    
	return df

def today(df, region):
	pass

def update_and_save():

	italia, regioni = update()

	italia = process(italia, 'Italia')
	italia.to_csv('data/italia.csv', index=False)
	today(italia, 'Italia')

	for region in REGIONS:
		df = process(regioni, region)
		df.to_csv(f'data/{region.lower()}.csv', index=False)
		today(df, region)

	return

update_and_save()
