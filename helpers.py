import matplotlib.pyplot as plt


from flask import redirect, session
from functools import wraps

import pandas as pd
import numpy as np
import seaborn as sns


# constants
START_DATE = '2020-01-22'
WINDOW = 7  # used for the moving average calc

URL_INFECT = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'

URL_DEATH = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
URL_POPULATION = 'https://raw.githubusercontent.com/owid/covid-19-data/master/scripts/input/un/population_latest.csv' 

LIMIT = -20000   # cut-off value for showing effects of post adjustments in the graph
SCALE = 1000000  # cases per SCALE (million) people
#RESULTS_DIR = 'static/img/graph'

# setting seaborn formatting
sns.set_context('notebook', rc={"axes.titlesize": 30})
sns.set_style('white')

def get_all_country_list():
    ## reading data
    fatalities = pd.read_csv(URL_DEATH)
    population = pd.read_csv(URL_POPULATION)
    country_list_population = population.entity.unique()

    translating_country_dict = {
        'US': 'United States',
        'Korea, South': 'South Korea',
        'Taiwan*': 'Taiwan'
    }
    fatalities = fatalities.replace({'Country/Region':translating_country_dict})


    all_country_list=[country for country in country_list_population if country in list(fatalities['Country/Region'].unique())]
    return all_country_list
      


def draw_graphs(country_list):
    # setting seaborn formatting
    sns.set_context('notebook', rc={"axes.titlesize": 30})
    sns.set_style('white')
    plt.switch_backend('agg')
    
    # read files
    fatalities = pd.read_csv(URL_DEATH)
    population = pd.read_csv(URL_POPULATION)
    infect = pd.read_csv(URL_INFECT)
    
    # simplify column names
    fatalities.rename(columns = {'Country/Region':'Country', 'Province/State':'Province'}, inplace=True)
    infect.rename(columns = {'Country/Region':'Country', 'Province/State':'Province'}, inplace=True)
    population = population.rename(columns={'entity':'Country', 'iso_code': 'iso3', 'population':'Population'})
    
    translating_country_dict = {
        'US': 'United States',
        'Korea, South': 'South Korea',
        'Taiwan*': 'Taiwan'
    }
    fatalities = fatalities.replace({'Country':translating_country_dict})
    infect = infect.replace({'Country':translating_country_dict})
       
    filtered_data = []
    
    # preparation of the infect and fatalities dataframes for calculating data
    input_dataframes = [infect, fatalities]
    
    for dataframe in input_dataframes:
        # melting data to long format
        df = dataframe.melt(id_vars=['Province', 'Country', 'Lat', 'Long'], var_name=['date'], value_name='cum_cases')
        df['date'] = pd.to_datetime(df['date'])
        
        # Making all data country level
        df = df.groupby(['Country', 'date']).agg({'cum_cases':sum}).reset_index()

        df = df.merge(population[['Country', 'Population']], on='Country', how='left')
        
        df = df.sort_values(by=['Country', 'date'])
        
        # calculating daily new cases from the cumulative numbers
        df['new_cases']= df['cum_cases'].diff() # however, the first day has to be dealt separately
        df.loc[df['date'] == '2020-01-22', 'new_cases'] = df['cum_cases']  # the first day of the infection of one country should equal the cumulative amount  
        
        #TODO itt is még hard codolva van a dátum
        # add rolling avg column
        df['moving_avg_new_cases'] = df['new_cases'].rolling(window=WINDOW).mean()

        # correcting first 5 days (it can be incorrect as the last days of the previous country can impact the rolling mean)
        df.loc[df['date'] <= '2020-01-27', 'moving_avg_new_cases'] = np.nan
        # population relative moving average
        df['pop_relative_moving_avg'] = df['moving_avg_new_cases'] / df['Population'] * SCALE
        
        filtered_df_data = df[df.Country.isin(country_list)]
        filtered_data.append(filtered_df_data)



    def plot_graph(filtered_data, label):
        plt.figure().clear()
        ax = sns.relplot(data=filtered_data, kind='line', x='date', y='pop_relative_moving_avg', hue='Country', palette=["firebrick", "midnightblue"], height=5, aspect=2)

        ax.set(xlabel= '', 
            ylabel = 'Cases', 
            #title = 'Rolling average of new infections per 1 million people '
            )
        plt.xticks(rotation=45)
        sns.despine(top=True, right=True)

        graphname = "static/img/graphs/" + label + ".png"
        plt.savefig(graphname)
        return graphname
    
    # preparing the graphs: first, get the data of the required countries
    graph_infection = plot_graph(filtered_data[0], 'infection')
    graph_fatalities = plot_graph(filtered_data[1], 'fatalities')

    return graph_infection, graph_fatalities