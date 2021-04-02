import datetime as dt

from sh import git
import update


def run():
    # update webiste content
    covid_IT, covid_RG, vaccines = update.get_data()
    covid_IT, covid_RG = update.preprocess_data(covid_IT, covid_RG)
    update.plot_data(covid_IT, covid_RG, vaccines)
    update.daily(covid_IT, covid_RG, vaccines)

    # commit changes
    now = dt.datetime.now().strftime('%H:%M %Y-%m-%d')
    print(f'Update: {now}')

    git('add', '.')
    git('commit', '-m', now)
    git('push')

    return


if __name__ == "__main__":
    run()
