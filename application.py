
import csv
from flask import Flask, redirect, render_template, request
from datetime import datetime
import pandas as pd
import seaborn as sns

from helpers import draw_covid_graph



# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


#@ app.route("/", methods=["GET"])

@ app.route("/", methods=["GET", "POST"])
def covid():
    """Get countries for checking covid data"""

    # get list of all the reported countries from a csv. This will be used by the form as the potential countries, from where the user can choose
    country_file = "countries.csv"
    countries = []
    with open(country_file) as f:
        reader = csv.reader(f)
        for line in reader:  # the countries are a list in one line
            for country in line:
                countries.append(country)

    # this is reported to Johns Hopkins but no population data exists so cannot be displayed in per capita graphs

    if request.method == "GET":  # display form
        message = ""
        return render_template("covid.html", message=message, countries=countries)

    else:  # the form has been posted
        country_list = []

        # collect countries from the form
        country1 = request.form.get("country1")
        country2 = request.form.get("country2")
        country3 = request.form.get("country3")

        if not not country1:  # ez tudom h nagyon csúnya, egyesével appendálom, ha submittáltak ilyet
            country_list.append(country1)

        if not not country2:
            country_list.append(country2)

        if not not country3:
            country_list.append(country3)

        for country in country_list:
            # if not a valid country, they should be dropped. after this step, the country_ist countains the valid country choices of the user
            if country == '' or country not in countries:
                country_list.remove(country)

        # makes one single string from the selected countries separated with comas to display it on the website
        countrystring = ""
        for i in range(len(country_list)):

            if i == len(country_list)-1:
                countrystring += " " + country_list[i]
            elif i == len(country_list)-2:  # there are other countries coming, we need a coma
                countrystring += " " + country_list[i] + " and"
            else:
                countrystring += " " + country_list[i] + ","

        message = "COVID status for " + countrystring
        graph_infect, graph_death = draw_covid_graph(country_list)

        return render_template("covid_results.html", message=message, countries=countries, graph_infect=graph_infect, graph_death=graph_death)
