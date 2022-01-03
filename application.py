

from flask import Flask, redirect, render_template, request


from helpers import draw_graphs, get_all_country_list



# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


@ app.route("/", methods=["GET", "POST"])
def covid():
  
    """Ask for countries and get COVID data displaying plots on infections and fatalities"""
    countries = get_all_country_list()

    
    if request.method == "GET":  # display form
        message = ""
        return render_template("covid.html", message=message, countries=countries)

    else:  # the form has been posted
        country_list = []

        # collect countries from the form
        country1 = request.form.get("country1")
        country2 = request.form.get("country2")
        

        if not not country1:  # checking whether a valid country has been selected
            country_list.append(country1)

        if not not country2:
            country_list.append(country2)

        for country in country_list:
            # if not a valid country, they should be dropped. after this step, the country_list countains the valid country choices of the user
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
        
        graph_infection, graph_fatalities = draw_graphs(country_list)
        
        #return render_template("covid_results.html", message=message, countries=countries)
        # ezt vettem ki
        return render_template("covid_results.html", message=message, countries=countries, graph_infection=graph_infection, graph_fatalities=graph_fatalities)
