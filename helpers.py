import matplotlib.pyplot as plt
from countryinfo import CountryInfo
import wget
from flask import redirect, session
from functools import wraps
import os
import csv
import numpy as np


def draw_covid_graph(country_list):
    """draws a graph from the countries in a list"""

    # constants
    START_DATE = '2020-01-22'
    WINDOW = 7  # used for the moving average calc
    URL_INFECT = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'

    URL_DEATH = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
    INFECT_CSV_NAME = "covid19_infect_global.csv"
    DEATH_CSV_NAME = "covid19_death_global.csv"

    LIMIT = -20000   # cut-off value for showing effects of post adjustments in the graph
    SCALE = 1000000  # cases per SCALE (million) people
    RESULTS_DIR = 'static/img/graph'

    def prepare_infect_graph(country_list):
        infect_datafile = wget.download(URL_INFECT, INFECT_CSV_NAME)
        filtered_data = filter_data(country_list, infect_datafile)
        os.remove(INFECT_CSV_NAME)  # removes datafile
        infect_graph = plot_graph(filtered_data, "infections")
        # plt.figure().clear()  # clear plot
        return infect_graph

    def prepare_death_graph(country_list):
        death_datafile = wget.download(URL_DEATH, DEATH_CSV_NAME)
        filtered_data = filter_data(country_list, death_datafile)
        os.remove(DEATH_CSV_NAME)  # removes datafile
        death_graph = plot_graph(filtered_data, "deaths")
        return death_graph

    # the following function puts together a dictionary for each country incl. daily cases, mov. average, covid days and outputs the list of country dictionaries

    def filter_data(country_list, datafile):
        filtered_data = []
        for i in range(len(country_list)):
            country = country_list[i]
            cases_list = load_values_aggregate(
                country, datafile)  # collects data from datafile

            covid_days = count_covid_period(cases_list)
            # calculates the new daily cases per capita
            daily_cases_pc = count_new_daily_cases_pc(country, cases_list)
            # calculates a moving average per capita and puts them into a list
            moving_avg_pc = calc_moving_avg_pc(daily_cases_pc)

            # puts these into a dictionary:
            country_data = {
                'name': country,
                'daily_new_cases_per_capita': daily_cases_pc,
                'moving_average_per_capita': moving_avg_pc,
                'nr of covid days': covid_days,
            }

            filtered_data.append(country_data)
        return filtered_data

    # this function below collects the values relating a country from the datafile in a list and returns a cases list for that specific country
    def load_values_aggregate(country, datafile):
        with open(datafile) as f:  # this is only necessary to calculate the number of days
            reader = csv.reader(f)
            for line in reader:
                # creates a list of zeros as many as days in the datafile
                cases_list = [0] * (len(line)-4)

        with open(datafile) as f:
            reader = csv.reader(f)
            for line in reader:
                if line[1] == country:
                    # the indexes 0-3 cover region, state, longitude & latitude, the daily case
                    for i in range(len(line)-4):
                        # data are from index 4.
                        # this adds the value of a region to the existing list
                        cases_list[i] = cases_list[i] + int(line[i+4])
                    # print("load values lines: ", line)
        return cases_list

    def count_covid_period(cases_list):  # counts non-zero elements
        covid_day = 0
        free_day = 0
        for daily_case in cases_list:
            if daily_case != 0:
                covid_day += 1
            else:
                free_day += 1
        return covid_day

    # this function puts together a list of per capita new daily cases for a given country
    def count_new_daily_cases_pc(country, cases_list):
        daily_cases_pc = []

        # In some cases, CountryInfo has a slightly different name for countries, therefore this has to be adjusted
        # original name in Johns Hopkins's list:
        JH_list = ["Bahamas", "Cabo Verde",
                   "Congo (Brazzaville)", "Congo (Kinshasa)", "Cote d'Ivoire", "Czechia", "Gambia", "Korea, South", "Micronesia", "North Macedonia", "Sao Tome and Principe", "Taiwan*", "Timor-Leste"]
        CI_list = ["The Bahamas", "Cape Verde", "Republic of the Congo", "Democratic Republic of the Congo", "Ivory Coast", "Czech Republic",
                   "The Gambia", "South Korea", 'Federated States of Micronesia', 'Republic of Macedonia', 'São Tomé and Príncipe', 'Taiwan', 'East Timor']

        # this loop goes through the JH list and if the given country is in the JH list (list of different country names for Johns Hopkins), it will replace it with the corresponding item in the country info list

        for i in range(len(JH_list)):
            if country == JH_list[i]:
                country = CI_list[i]

        population = CountryInfo(country).population()
        # print("population is in average: " + country)
        # print(population)

        for i in range(len(cases_list)):
            if i == 0:  # the first day does not have a preceding data
                daily_cases_pc.append(cases_list[i]/population * SCALE)
            else:
                # to limit post adjustment effects
                daily_nr = max(
                    (cases_list[i] - cases_list[i - 1])/population * SCALE, LIMIT/population * SCALE)
                daily_cases_pc.append(daily_nr)

        # print(daily_cases_pc)
        return daily_cases_pc

    def calc_moving_avg_pc(daily_cases_pc):

        moving_avg = []

        for i in range(len(daily_cases_pc)):
            tmp_sum = 0
            counter = 0

            window_start = max(i - WINDOW + 1,
                               0)  # this is the first index which should be included in the window of the moving avg
            window_length = i - window_start + 1
            for j in range(window_start, i + 1):  # i+1 not included
                tmp_sum += daily_cases_pc[j]
                counter += 1

            mvg_avg = tmp_sum / counter
            moving_avg.append(mvg_avg)
        return moving_avg

    def plot_graph(filtered_data, label):
        # this prepares a graph from the country dictionaries (filetered data), label should be a string: "infect" or "death" and
        # will appear both on the y axis and in the filename of the saved graph

        # the below line is necessary so that tkinter does not run onto error (per stackflow advice)
        plt.switch_backend('agg')

        for i in range(len(filtered_data)):
            # here i populate a numpy array from the days elapsed since 2020-01-22 (this is the start of the covid data)
            start_date = np.array(START_DATE, dtype=np.datetime64)
            nr_of_days_elapsed = len(
                filtered_data[i]['daily_new_cases_per_capita'])
            days = start_date + np.arange(nr_of_days_elapsed)

            label_avg = filtered_data[i]['name']

            plt.rcParams["figure.figsize"] = (11, 5)
            plt.plot(
                days, filtered_data[i]['moving_average_per_capita'], label=label_avg)
            # this makes the plot readable and twice as wide as high

        plt.legend()

        #plt.title('New daily covid cases ' + str(WINDOW) + " days average per 1 million people")
        plt.grid(axis='y', linestyle='--')
        plt.xlabel('Time')
        plt.ylabel(label)

        # saving the png to local
        # script_dir = os.path.dirname(__file__)

        graphname = "static/img/graph_" + label + ".png"
        plt.savefig(graphname)

        plt.figure().clear()
        return graphname

    graph_infect = prepare_infect_graph(country_list)
    graph_death = prepare_death_graph(country_list)

    return graph_infect, graph_death
