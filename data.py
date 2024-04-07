# import requests
# import json
# headers = {"Authorization": "Bearer sk_prod_GztzSEBgJvRQXyoyv4GX7bfW5KuVAjbNcOjzG4KgglJcXXEfMIUWBSv2JqxAhhS18ecsIF0VPHgKzBAMdK9jIzhtaO5U1ovkQTK_4078"}
# submissions = requests.get(f"https://api.fillout.com/v1/api/forms/x29P9cvL4wus/submissions", headers=headers)
# submissions = json.loads(submissions.text)

import pandas
import googlemaps

gmaps = googlemaps.Client(key='AIzaSyCyRQ3xTOLkHkgLjqwg9rCtrgoWcRpzOJA')

df = pandas.read_csv("static/20240325.csv")
df = df.loc[:, "What is the street address of your apartment?": "id"]
breakpoint
addresses = df["What is the street address of your apartment?"]

latitudes = []
longitudes = []
for address in addresses:
    geocode = gmaps.geocode(address)[0]["geometry"]["location"]
    latitudes.append(geocode["lat"])
    longitudes.append(geocode["lng"])
df["lat"] = latitudes
df["lng"] = longitudes

df.to_json("static/data.json", orient="records")