import os

import datetime as dt
from fuzzyfinder import fuzzyfinder
import numpy as np
import pandas as pd

from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

plt.rcParams['figure.figsize'] = (12, 8)

with open('regions.txt', 'r') as f:
    REGIONS = eval(f.read())

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


def get_data():
    # COVID data
    base_url = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/'
    url_IT = base_url + 'dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv'
    url_RG = base_url + 'dati-regioni/dpc-covid19-ita-regioni.csv'

    to_drop = ['stato',
               'isolamento_domiciliare',
               'casi_da_sospetto_diagnostico',
               'casi_da_screening',
               'note',
               'note_test',
               'note_casi',
               'totale_positivi_test_molecolare',
               'totale_positivi_test_antigenico_rapido',
               'tamponi_test_molecolare',
               'tamponi_test_antigenico_rapido',
               'casi_testati',
               'ingressi_terapia_intensiva',
               'totale_ospedalizzati'
    ]
    covid_IT = pd.read_csv(url_IT).drop(to_drop, axis=1)
    covid_RG = pd.read_csv(url_RG).drop(to_drop, axis=1)

    to_datetime = lambda x: dt.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")
    covid_IT['data'] = covid_IT.data.map(to_datetime)
    covid_RG['data'] = covid_RG.data.map(to_datetime)

    covid_IT.sort_values('data', inplace=True)
    covid_RG.sort_values('data', inplace=True)
    covid_IT = covid_IT[covid_IT.data >= dt.datetime(2020, 9, 26)].reset_index(drop=True)
    covid_RG = covid_RG[covid_RG.data >= dt.datetime(2020, 9, 26)].reset_index(drop=True)

    columns_map = {
        'ricoverati_con_sintomi'     : 'tot_sintomi',
        'terapia_intensiva'          : 'tot_intensiva',
        'totale_positivi'            : 'tot_positivi',
        'variazione_totale_positivi' : 'net_positivi',
        'nuovi_positivi'             : 'gross_positivi',
        'totale_casi'                : 'cdf_positivi',
        'dimessi_guariti'            : 'tot_guariti',
        'deceduti'                   : 'tot_morti',
        'tamponi'                    : 'tot_tamponi',
    }

    covid_IT.rename(columns=columns_map, inplace=True)
    covid_RG.rename(columns=columns_map, inplace=True)

    # VACCINE data
    base_url = 'https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/'
    url_SUMM = 'somministrazioni-vaccini-summary-latest.csv'

    vaccines = pd.read_csv(base_url + url_SUMM).sort_values('data_somministrazione')
    vaccines.reset_index(drop=True, inplace=True)

    to_datetime = lambda x: dt.datetime.strptime(x, "%Y-%m-%d")

    prima, seconda, data, regione = [], [], [], []
    for date in set(vaccines.data_somministrazione):
        daily = vaccines[vaccines.data_somministrazione == date].copy()
        for region in set(vaccines.nome_area):

            prima.append(daily[daily.nome_area == region]['prima_dose'].sum())
            seconda.append(daily[daily.nome_area == region]['seconda_dose'].sum())

            if '/' in region: region = region.split(' / ')[0]
            if 'Provincia' in region: region = 'P.A. ' + region.split(' ')[2]

            regione.append(list(fuzzyfinder(region, REGIONS))[0])
            data.append(to_datetime(date))

        data.append(to_datetime(date))
        prima.append(daily['prima_dose'].sum())
        seconda.append(daily['seconda_dose'].sum())
        regione.append('Italia')

    vaccines = pd.DataFrame(data={'data': data, 'prima_dose': prima,
                                  'seconda_dose': seconda, 'regione': regione})
    vaccines['totale'] = vaccines.prima_dose + vaccines.seconda_dose
    vaccines.sort_values('data', inplace=True)

    return covid_IT, covid_RG, vaccines


def preprocess_data(covid_IT, covid_RG):
    # average period
    avgp = 7

    # ITALY
    # compute net daily data
    covid_IT['net_sintomi'] = covid_IT.tot_sintomi - covid_IT.tot_sintomi.shift(1,fill_value=0)
    covid_IT['net_intensiva'] = covid_IT.tot_intensiva - covid_IT.tot_intensiva.shift(1,fill_value=0)

    covid_IT['net_guariti'] = covid_IT.tot_guariti - covid_IT.tot_guariti.shift(1,fill_value=0)
    covid_IT['net_morti'] = covid_IT.tot_morti - covid_IT.tot_morti.shift(1,fill_value=0)

    covid_IT['net_tamponi'] = covid_IT.tot_tamponi - covid_IT.tot_tamponi.shift(1,fill_value=0)

    covid_IT.drop([0]).reset_index(drop=True, inplace=True)

    # moving averages
    covid_IT['wma_gross_positivi'] = (covid_IT.gross_positivi*covid_IT.net_tamponi).rolling(avgp, min_periods=0).sum()
    covid_IT['wma_gross_positivi'] = covid_IT.wma_gross_positivi / covid_IT.net_tamponi.rolling(avgp, min_periods=0).sum()

    # compute statistical errors
    covid_IT['delta_gross_positivi'] = np.sqrt(covid_IT.gross_positivi * (1 - covid_IT.gross_positivi/covid_IT.net_tamponi))
    covid_IT['delta_wma_gross_positivi'] = (covid_IT.delta_gross_positivi*covid_IT.net_tamponi).rolling(avgp, min_periods=0).sum()
    covid_IT['delta_wma_gross_positivi'] = covid_IT.delta_wma_gross_positivi / covid_IT.net_tamponi.rolling(avgp, min_periods=0).sum()

    covid_IT.drop([0, 1, 2, 3, 4], inplace=True)

    # REGIONS
    friuli = lambda x: 'Friuli-Venezia Giulia' if x == 'Friuli Venezia Giulia' else x
    covid_RG.denominazione_regione = covid_RG.denominazione_regione.map(friuli)
    for region in REGIONS:
        df = covid_RG[covid_RG.denominazione_regione == region].reset_index(drop=True)

        # compute net daily data
        df['net_sintomi'] = df.tot_sintomi - df.tot_sintomi.shift(1,fill_value=0)
        df['net_intensiva'] = df.tot_intensiva - df.tot_intensiva.shift(1,fill_value=0)

        df['net_guariti'] = df.tot_guariti - df.tot_guariti.shift(1,fill_value=0)
        df['net_morti'] = df.tot_morti - df.tot_morti.shift(1,fill_value=0)

        df['net_tamponi'] = df.tot_tamponi - df.tot_tamponi.shift(1,fill_value=0)

        df.drop([0]).reset_index(drop=True, inplace=True)

        # moving averages
        df['wma_gross_positivi'] = (df.gross_positivi*df.net_tamponi).rolling(avgp, min_periods=0).sum()
        df['wma_gross_positivi'] = df.wma_gross_positivi / df.net_tamponi.rolling(avgp, min_periods=0).sum()

        # compute statistical errors
        df['delta_gross_positivi'] = np.sqrt(df.gross_positivi * (1 - df.gross_positivi/df.net_tamponi))
        df['delta_wma_gross_positivi'] = (df.delta_gross_positivi*df.net_tamponi).rolling(avgp, min_periods=0).sum()
        df['delta_wma_gross_positivi'] = df.delta_wma_gross_positivi / df.net_tamponi.rolling(avgp, min_periods=0).sum()

        df.drop([0, 1, 2, 3, 4], inplace=True)

        try:
            covid_RG_merged = pd.merge(covid_RG_merged, df, how='outer')
        except NameError:
            covid_RG_merged = df.copy()

    return covid_IT, covid_RG_merged


def plot_data(covid_IT, covid_RG, vaccines):
    # plot Italia

    days = mdates.DayLocator()
    fifteen_days = mdates.DayLocator(bymonthday=[1, 15])
    fifteen_days_fmt = mdates.DateFormatter('%d %b')

    for region in REGIONS + ['Italia']:
        pp = PdfPages(f'plots/{region.lower()}.pdf')

        if region == 'Italia':
            df = covid_IT.copy()
        else:
            df = covid_RG[covid_RG.denominazione_regione == region].copy()

        x = df.data.values

        y = df.wma_gross_positivi.values
        delta_y = df.delta_wma_gross_positivi.values

        fig, ax = plt.subplots()

        # set formatters for x axis
        ax.xaxis.set_major_locator(fifteen_days)
        ax.xaxis.set_major_formatter(fifteen_days_fmt)
        ax.xaxis.set_minor_locator(days)

        ax.scatter(x, y, s=49, marker='.', color='b')
        ax.fill_between(x, y - 3*delta_y, y + 3*delta_y, color='b', alpha=0.2)

        ax.grid()
        ax.set_ylabel('Incremento POSITIVI', fontsize=16)
        ax.tick_params(axis='y', labelcolor='b')

        ax1 = ax.twinx()  # instantiate a second axes that shares the same x-axis

        ax1.xaxis.set_major_locator(fifteen_days)
        ax1.xaxis.set_major_formatter(fifteen_days_fmt)
        ax1.xaxis.set_minor_locator(days)

        ax1.scatter(x, df.net_morti.rolling(7, min_periods=0).mean(), marker='.', s=49, color='r')
        ax1.set_ylabel('Incremento DECEDUTI', fontsize=16)
        ax1.tick_params(axis='y', labelcolor='r')
        plt.title('Medie mobili a 7 giorni', fontsize=16)
        pp.savefig()
        plt.close(fig)

        fig, ax = plt.subplots()

        # set formatters for x axis
        ax.xaxis.set_major_locator(fifteen_days)
        ax.xaxis.set_major_formatter(fifteen_days_fmt)
        ax.xaxis.set_minor_locator(days)

        ax.scatter(x, df.net_sintomi.rolling(7, min_periods=0).mean(), s=49, marker='.', color='b')

        ax.grid()
        ax.set_ylabel('Incremento RICOVERATI CON SINTOMI', fontsize=16)
        ax.tick_params(axis='y', labelcolor='b')

        ax1 = ax.twinx()  # instantiate a second axes that shares the same x-axis

        ax1.xaxis.set_major_locator(fifteen_days)
        ax1.xaxis.set_major_formatter(fifteen_days_fmt)
        ax1.xaxis.set_minor_locator(days)

        ax1.scatter(x, df.net_intensiva.rolling(7, min_periods=0).mean(), marker='.', s=49, color='r')
        ax1.set_ylabel('Incremento ricoveri TERAPIA INTENSIVA', fontsize=16)
        ax1.tick_params(axis='y', labelcolor='r')
        plt.title('Medie mobili a 7 giorni', fontsize=16)
        pp.savefig()
        plt.close(fig)

        fig, ax = plt.subplots()

        # set formatters for x axis
        ax.xaxis.set_major_locator(fifteen_days)
        ax.xaxis.set_major_formatter(fifteen_days_fmt)
        ax.xaxis.set_minor_locator(days)

        ax.scatter(x, y, s=49, marker='.', color='b')
        ax.fill_between(x, y - 3*delta_y, y + 3*delta_y, color='b', alpha=0.2)

        ax.grid()
        ax.set_ylabel('Incremento POSITIVI', fontsize=16)
        ax.tick_params(axis='y', labelcolor='b')

        ax1 = ax.twinx()  # instantiate a second axes that shares the same x-axis

        ax1.xaxis.set_major_locator(fifteen_days)
        ax1.xaxis.set_major_formatter(fifteen_days_fmt)
        ax1.xaxis.set_minor_locator(days)

        ax1.scatter(x, df.net_sintomi.rolling(7, min_periods=0).mean(), marker='.', s=49, color='r')
        ax1.set_ylabel('Incremento RICOVERATI CON SINTOMI', fontsize=16)
        ax1.tick_params(axis='y', labelcolor='r')
        plt.title('Medie mobili a 7 giorni', fontsize=16)
        pp.savefig()
        plt.close(fig)

        fig, ax = plt.subplots()

        vacc_region = vaccines[vaccines.regione == region].copy()
        # set formatters for x axis
        ax.xaxis.set_major_locator(fifteen_days)
        ax.xaxis.set_major_formatter(fifteen_days_fmt)
        ax.xaxis.set_minor_locator(days)

        ax.bar(vacc_region.data, vacc_region.prima_dose, label='Prima dose')
        ax.bar(vacc_region.data, vacc_region.seconda_dose,
               bottom=vacc_region.prima_dose, label='Seconda dose')

        ax.set_ylabel('DOSI VACCINO somministrate', fontsize=16)
        if region == 'Italia':
            ax.set_yticks([25e3*i for i in range(max(vacc_region.totale) // 25000 + 1)])
        ax.legend()
        ax.grid()
        pp.savefig()
        plt.close(fig)

        pp.close()

        os.system(f'pdf2svg "plots/{region.lower()}.pdf" "images/{region.lower()}/{region.lower()}%d.svg" all')

    return


def format_vaccine(totale, prima_dose):
    formatted = []
    for x, y in zip(totale, prima_dose):
        formatted.append(f'{x}({y})')
    return formatted


def format_date(x):
    day, month = x.split(' ')
    if day[0] == '0': day = day[1]
    month = MONTHS.get(month)

    return f'{day} {month}'


def daily(covid_IT, covid_RG, vaccines):
    for region in REGIONS + ['Italia']:
        if region == 'Italia':
            df = covid_IT.copy()
        else:
            df = covid_RG[covid_RG.denominazione_regione == region].copy()

        vacc_region = vaccines[vaccines.regione == region].tail(3).set_index('data')
        vacc_region.index = vacc_region.index.map(lambda x: x.strftime('%d %B'))
        vacc_region.index = vacc_region.index.map(format_date)

        df = df.tail(2).set_index('data')
        df.index = df.index.map(lambda x: x.strftime('%d %B'))
        df.index = df.index.map(format_date)

        df = df[['gross_positivi', 'net_positivi', 'net_tamponi', 'net_morti',
                 'net_guariti', 'net_sintomi', 'net_intensiva']]
        df['Rapporto POSITIVI-TAMPONI'] = (df.gross_positivi/df.net_tamponi*100).map(lambda x: round(x, 1))
        vacc_region = vacc_region.loc[df.index.tolist()].copy()
        df['VACCINI somministrati (di cui PRIMA DOSE)'] = format_vaccine(vacc_region.totale, vacc_region.prima_dose)
        df = df.rename(columns={
                'gross_positivi': 'Nuovi POSITIVI',
                'net_positivi'  : 'Incremento NETTO POSITIVI',
                'net_tamponi'   : 'Incremento TAMPONI',
                'net_morti'     : 'Incremento MORTI',
                'net_guariti'   : 'Incremento GUARITI',
                'net_sintomi'   : 'Incremento RICOVERATI con SINTOMI',
                'net_intensiva' : 'Incremento TERAPIA INTENSIVA'})
        df.index.rename('', inplace=True)

        df['Rapporto POSITIVI-TAMPONI'] = df['Rapporto POSITIVI-TAMPONI'].map(lambda x: f'{str(x)} %')

        df = df.T
        for column in df.columns:
            df[column] = df[column].map(lambda x: int(x) if (type(x) is not type('covid')) else x)

        # injecting html
        if region == 'Italia': file_ = 'index.html'
        else: file_ = f'website/regions/{region.lower()}.html'
        with open(file_, 'r') as f: html = f.read()

        html0 = html.split('class="flag">')[0]
        html1 = html.split('</table>')[1]
        html = html0 + 'class="flag">' + '\n' + df.to_html() + html1

        with open(file_, 'w') as f: f.write(html)

    return

get_data()