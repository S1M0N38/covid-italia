import datetime as dt
import numpy    as np
import pandas   as pd

import time

MONTHS = {
	'January'   : 'Gen', 
	'February'  : 'Feb', 
	'March'     : 'Mar', 
	'April'     : 'Apr', 
	'May'       : 'Mag',
    'June'      : 'Giu',
    'July'      : 'Lug',
    'August'    : 'Ago',
	'September' : 'Set', 
	'October'   : 'Ott', 
	'November'  : 'Nov', 
	'December'  : 'Dic' 
}

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

	df['tamponi'] = df.tamponi - df.tamponi.shift(1, fill_value=0)
	df['tamponi'] = df.tamponi.map(int)

	df = df.drop([0]).reset_index()
	df = df[['data', 'totale_casi', 'positivi', 'netto_positivi', 'tamponi', 'guariti', 
	         'totale_positivi', 'morti', 'sintomi', 'intensiva', 'delta_positivi']].copy()
    
	return df

def format_date(x):
	day, month = x.split(' ')

	if day[0] == '0': day = day[1]
	month = MONTHS.get(month)

	return f'{day} {month}'

def to_int(x):
	x = float(x)
	if x - int(x) > 0:
		return f'{str(x)} %'
	else: return str(int(x))

def today(df, region):
	df = df.tail(2).set_index('data')
	df.index = df.index.map(lambda x: x.strftime('%d %B'))
	df.index = df.index.map(format_date)

	# TODO select columms and change column name, maybe color for today and for col
	df = df[['positivi', 'netto_positivi', 'tamponi', 'morti', 'guariti', 'sintomi', 'intensiva']]
	df['Rapporto POSITIVI-TAMPONI'] = (df.positivi/df.tamponi*100).map(lambda x: round(x, 1))
	df = df.rename(columns={
		'positivi'       : 'Nuovi POSITIVI',
		'netto_positivi' : 'Incremento NETTO POSITIVI',
		'tamponi'        : 'Incremento TAMPONI', 
		'morti'          : 'Incremento MORTI',
		'guariti'        : 'Incremento GUARITI',
		'sintomi'        : 'Incremento RICOVERATI con SINTOMI',
		'intensiva'      : 'Incremento TERAPIA INTENSIVA'})
	df.index.rename('', inplace=True)

	df = df.T
	for column in df.columns:
		df[column] = df[column].map(str).map(to_int)

	# injecting html
	if region == 'Italia': 
		file_ = 'index.html'
	else: file_ = f'website/regions/{region.lower()}.html'
	with open(file_, 'r') as f: html = f.read()

	html0 = html.split('class="flag">')[0]
	html1 = html.split('</table>')[1]
	html = html0 + 'class="flag">' + '\n' + df.to_html() + html1

	with open(file_, 'w') as f: f.write(html)
	return


def update_and_save():

	italia, regioni = update()

	for region in REGIONS:
		if region == 'Italia': df = process(italia, 'Italia')
		else: df = process(regioni, region)
		df.to_csv(f'data/{region.lower()}/{region.lower()}.csv', index=False)
		today(df, region)

	return

if __name__ == "__main__":
	update_and_save()
