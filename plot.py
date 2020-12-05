from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.dates  as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

plt.rcParams['figure.figsize'] = (8, 6)

import os

import datetime as dt
import numpy    as np
import pandas   as pd

from scipy.optimize import curve_fit

N0 = 0

def gompertz(t, alpha, Ninf, t0):
	return Ninf * (N0 / Ninf)**(np.exp(-alpha*(t-t0)))

def logistic(t, alpha, Ninf, t0):
	return Ninf / (1 + np.exp(-alpha*(t-t0)))

def g_prime(t, alpha, Ninf, t0):
	return gompertz(t, alpha, Ninf, t0) * alpha * np.log(Ninf / gompertz(t, alpha, Ninf, t0))

def l_prime(t, alpha, Ninf, t0):
	return logistic(t, alpha, Ninf, t0) * alpha * (1 - logistic(t, alpha, Ninf, t0) / Ninf)

def load(region):
	# load data for region
	df = pd.read_csv(f'data/{region.lower()}/{region.lower()}.csv')
	to_datetime = lambda x: dt.datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
	df['data'] = df.data.map(to_datetime)
	return df.sort_values('data')

def plot(region):
	
	df = load(region)

	global N0 
	N0 = df.totale_casi.values[0]
	
	pp = PdfPages(f'plots/{region.lower()}.pdf')
	
	days = mdates.DayLocator()
	fifteen_days = mdates.DayLocator(bymonthday=[1,15])
	fifteen_days_fmt = mdates.DateFormatter('%d %b')
	
	X = df.index.values

	X_ = np.array(range(X[-1] + 20))
	data_ = np.array([np.datetime64(df.data.values[-1]) + np.timedelta64(i+1, 'D') for i in range(19)])
	data_ = np.append(df.data.values, data_)


	# INCREMENTO POSITIVI
	
	Y = df.positivi.rolling(5, min_periods=0).mean().values
	deltaY = df.delta_positivi.values
	
	popt_g, pcov = curve_fit(g_prime, X, Y, p0=[0.05, 1e6, 50])
	perr_g = np.sqrt(np.diag(pcov))
	
	popt_l, pcov = curve_fit(l_prime, X, Y, p0=[0.05, 1e6, 50])
	perr_l = np.sqrt(np.diag(pcov))

	fig, ax = plt.subplots()
	
	ax.xaxis.set_major_locator(fifteen_days)
	ax.xaxis.set_major_formatter(fifteen_days_fmt)
	ax.xaxis.set_minor_locator(days)
	
	ax.grid(True)
	fig.autofmt_xdate()
	
	ax.errorbar(df.data, Y, fmt='.', label='dati')
	ax.plot(data_, g_prime(X_, *popt_g), label='gompertz')
	ax.plot(data_, l_prime(X_, *popt_l), label='logistic')
	
	ax.set_ylabel('Incremento positivi', fontsize=16)
	plt.title('Media mobile a 5 giorni', fontsize=16)
	plt.legend()
	
	fig.tight_layout()  # otherwise the right y-label is slightly clipped

	pp.savefig()
	

	# TOTALE POSITIVI e INCREMENTO NETTO POSITIVI
	
	fig, ax1 = plt.subplots()
	
	ax1.xaxis.set_major_locator(fifteen_days)
	ax1.xaxis.set_major_formatter(fifteen_days_fmt)
	ax1.xaxis.set_minor_locator(days)
	
	ax1.grid(True)
	fig.autofmt_xdate()

	color = 'tab:blue'
	ax1.set_ylabel('Attualmente positivi', color=color, fontsize=16)
	ax1.plot(df.data, df.totale_positivi, '.-', color=color)
	ax1.tick_params(axis='y', labelcolor=color)

	ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
	
	ax2.xaxis.set_major_locator(fifteen_days)
	ax2.xaxis.set_major_formatter(fifteen_days_fmt)
	ax2.xaxis.set_minor_locator(days)

	color = 'tab:orange'
	ax2.set_ylabel('Incremento netto positivi', color=color, fontsize=16)
	ax2.plot(df.data, df.netto_positivi, '.-', color=color)
	ax2.tick_params(axis='y', labelcolor=color)

	fig.tight_layout()  # otherwise the right y-label is slightly clipped
	
	pp.savefig()
	
	
	# TAMPONI e RAPPORTO POSITIVI TAMPONI
	
	fig, ax1 = plt.subplots()
	
	ax1.xaxis.set_major_locator(fifteen_days)
	ax1.xaxis.set_major_formatter(fifteen_days_fmt)
	ax1.xaxis.set_minor_locator(days)
	
	ax1.grid(True)
	fig.autofmt_xdate()
	
	color = 'tab:blue'
	ax1.set_ylabel('Incremento tamponi', color=color, fontsize=16)
	ax1.plot(df.data, df.tamponi, '.-', color=color)
	ax1.tick_params(axis='y', labelcolor=color)
	
	ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
	
	ax2.xaxis.set_major_locator(fifteen_days)
	ax2.xaxis.set_major_formatter(fifteen_days_fmt)
	ax2.xaxis.set_minor_locator(days)
	
	ax2.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f%%'))

	color = 'tab:red'
	ax2.set_ylabel('Rapporto Positivi-Tamponi', color=color, fontsize=16)
	ax2.plot(df.data, df.positivi/df.tamponi*100, '.-', color=color)
	ax2.tick_params(axis='y', labelcolor=color)

	fig.tight_layout()  # otherwise the right y-label is slightly clipped
	
	pp.savefig()
	
	
	# PRESSIONE OSPEDALIERA
	
	# sintomi = df.sintomi.rolling(5, min_periods=0).mean()
	# intensiva = df.intensiva.rolling(5, min_periods=0).mean()
	
	fig, ax1 = plt.subplots()
	
	ax1.xaxis.set_major_locator(fifteen_days)
	ax1.xaxis.set_major_formatter(fifteen_days_fmt)
	ax1.xaxis.set_minor_locator(days)
	
	ax1.grid(True)
	fig.autofmt_xdate()

	color = 'tab:blue'
	ax1.set_ylabel('Incremento ricoverati con sintomi', color=color, fontsize=16)
	ax1.plot(df.data, df.sintomi, '.-', color=color)
	ax1.tick_params(axis='y', labelcolor=color)

	ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
	
	ax2.xaxis.set_major_locator(fifteen_days)
	ax2.xaxis.set_major_formatter(fifteen_days_fmt)
	ax2.xaxis.set_minor_locator(days)

	color = 'tab:red'
	ax2.set_ylabel('Incremento terapia intesiva', color=color, fontsize=16)
	ax2.plot(df.data, df.intensiva, '.-', color=color)
	ax2.tick_params(axis='y', labelcolor=color)

	# plt.title('Media mobile a 5 giorni', fontsize=16)

	fig.tight_layout() # otherwise the right y-label is slightly clipped
	
	pp.savefig()
	
	# MORTI e GUARITI
	
	fig, ax1 = plt.subplots()
	
	ax1.xaxis.set_major_locator(fifteen_days)
	ax1.xaxis.set_major_formatter(fifteen_days_fmt)
	ax1.xaxis.set_minor_locator(days)
	
	ax1.grid(True)
	fig.autofmt_xdate()

	color = 'tab:green'
	ax1.set_ylabel('Incremento guariti', color=color, fontsize=16)
	ax1.plot(df.data, df.guariti, '.-', color=color)
	ax1.tick_params(axis='y', labelcolor=color)

	ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
	
	ax2.xaxis.set_major_locator(fifteen_days)
	ax2.xaxis.set_major_formatter(fifteen_days_fmt)
	ax2.xaxis.set_minor_locator(days)

	color = 'tab:red'
	ax2.set_ylabel('Incremento morti', color=color, fontsize=16)
	ax2.plot(df.data, df.morti, '.-', color=color)
	ax2.tick_params(axis='y', labelcolor=color)

	fig.tight_layout()  # otherwise the right y-label is slightly clipped
	
	pp.savefig()
	
	pp.close()
	plt.close('all')
	
	return

with open('regions.txt', 'r') as f:
	REGIONS = eval(f.read())

if __name__ == "__main__":
	for region in REGIONS:
		plot(region)
		os.system(f'pdf2svg "plots/{region.lower()}.pdf" "images/{region.lower()}/{region.lower()}%d.svg" all')
