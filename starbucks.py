
import pandas as pd
from pandas import DataFrame, read_csv
import os
import folium
import webbrowser

from geopy import distance
from geopy.geocoders import Nominatim
from uszipcode import SearchEngine


STARBUCKS_FILE = "All_Starbucks_Locations_in_the_US.csv"
FILTERS = ('Store Number', 'Name', 'Street Address', 'City', 'State', 'Zip','Latitude','Longitude','Features - Stations')

debug = False
class Store(object):
    """
    Store object should have values for each column in FILTERS and distance.
    """
    def __init__ (self,row=None):
        self.number = row[1][0]
        self.name = row[1][1]
        self.address = row[1][2]
        self.city = row[1][3]
        self.state = row[1][4]
        self.zip = row[1][5]
        self.lat = row[1][6]
        self.long = row[1][7]
        if row[1][8] == "Drive-Through":
            self.dr = "YES"
        else:
            self.dr = "NO"
    #try if there is a column distance, if not distance =-1
        try:
            self.distance = row[1][9]
        except Exception:
            self.distance = -1
    #print out the store info
    def __str__ (self):
        #if distance = -1 then do not print out distance output
        if self.distance == -1:
            result = "Store ID: " + str(self.number) +"\t" + self.name + "\n" + self.address + "\n" + self.city +", " +self.state + " " + self.zip + "\n("+ str(self.lat) +", " + str(self.long) + ")" + "\nDrive-Through: " + self.dr
        else:
            result = "Store ID: " + str(self.number) +"\t" + self.name + "\n" + self.address + "\n" + self.city +", " +self.state + " " + self.zip + "\n("+ str(self.lat) +", " + str(self.long) + ")" + "\nDrive-Through: " + self.dr +"\nDistance: " + "%0.2f"%self.distance+" miles"
        return result


def getData():
    df = pd.read_csv(STARBUCKS_FILE)
    df = df.filter(FILTERS)
    return df

def displayMap(dfStores):
    """
        display a map
        See https://python-visualization.github.io/folium/ for documentation
    """
    # get the average latitude and longitude values from dfStore
    avg_lat = dfStores['Latitude'].mean()
    avg_lon = dfStores['Longitude'].mean()

    # create lists of lats, longs, names, and drivethru's
    lats =  [i for i in dfStores['Latitude']]
    lons = [i for i in dfStores['Longitude']]
    names = [i for i in dfStores['Name']]
    drivethrus = [i for i in dfStores['Features - Stations']]
    from folium import plugins

    # create a folium Map cetered at avg_lat and avg_lon

    foliumMap = folium.Map( location = [avg_lat, avg_lon], zoom_start=11)

    for i,item in enumerate(lats):
        # plot each lat, lon, and name on the map
        lat = lats[i]
        lon = lons[i]
        # change the color of the pin if it represents a store with a drive-thru
        if drivethrus[i] == "Drive-Through":
            icon = folium.Icon(icon="coffee",prefix="fa",color="green")
            dr = "Drive-Through"
        # create an Icon - see folium.Icon documentation constructor for options
        else:
            icon = folium.Icon(icon="coffee", prefix="fa", color='purple')
            dr = ""
        # create a Marker and add it to the map at lat, lon; set the marker text
        folium.Marker(location=[lat, lon],
                        popup = folium.Popup(names[i] + "<br>" + dr, max_width=200),
                        icon = icon).add_to(foliumMap)

    # write code to save the map as map.html in the current directory and launch it in a browser
    filePath = os.getcwd() + "\\map.html"
    foliumMap.save(filePath)
    print("Map located in: ",filePath)
    webbrowser.open('file://' + filePath)

def dfDisplay(df):
    #  print the number of stores found
    print(len(df.index),"stores found")
    print()
    # create a Store object from the row's values then print it
    for row in df.iterrows():
        row = Store(row)
        print(row.__str__())
        print()
        # row is a tuple so get the elements from it
        # row will have an extra column (distance) when finding stores by distance
        # distance will be in column 9 if the row has a column 9. (If out of range, set distance to  -1).

def findStoresByCityState(dfStores):
    while True:
        city = input("Enter a city: ").lower()
        state = input("Enter a state abbreviation: ").lower()
        if city == "" or state == "":
            print("Error. Enter a city and a state.")
        else:
            break
    # filter dfStores by City
    df = dfStores[dfStores['City'].str.lower() == city]
    # filter the result by State
    df = df.loc[df.State.str.lower() == state]
    # if no stores are found, print a message,
    if df.empty is True:
        print("Error. No stores are found \n")
    # otherwise print the list and the map
    else:
        dfDisplay(df)
        displayMap(df)

#search lat and long function by city and state
def latlongbycitysearch(city,state):
    search = SearchEngine()
    data = search.by_city_and_state(city,state)
    for i in data:
        zipcode = i.to_dict()
    lat = zipcode["lat"]
    long = zipcode ["lng"]
    return lat,long

#search lat and long function by zip
def latlongbyzipsearch(zipy):
    search = SearchEngine()
    zipcode = search.by_zipcode(zipy).to_dict()
    lat = zipcode["lat"]
    long = zipcode ["lng"]
    return lat,long

#find the distance between locations
def distanceBetweenLocations(loc1lat,loc1long,loc2lat,loc2long):
    geolocator = Nominatim(user_agent="My_Store_Finder")
    distancebetween = distance.distance((loc1lat,loc1long),(loc2lat,loc2long)).miles
    return distancebetween

def findStoresWithinDistanceCityState(dfStores):
    search = SearchEngine()
    miles = int(input("Search radius in miles: "))
    homeCity = input("Enter home city name: ")
    while True:
            state = input("Enter home state abbreviation: ")
            if state == "":
                print("Error: enter a state")
            else:
                break
    hasDriveThru = input("Only show stores with drive-thru? y/n ").lower()
# find the latitude/longitude for the city state
    try:
        lat,long = latlongbycitysearch(homeCity,state)
    except Exception:
        print("Error. Invalid city or state\n")
        return
# create a list of stores within specified number of miles
    data = search.by_coordinates(lat,long,radius=miles,returns=0)
    #append to a list
    ziplist = []
    for i in data:
        a = i.to_dict()
        ziplist.append(a["zipcode"])
    df = dfStores[dfStores["Zip"].str.contains("|".join(ziplist),na=False)].copy()
# calculate the distance from each store to the home city/state,
    distances = []
    for row in df.iterrows():
        row = Store(row)
        a = distanceBetweenLocations(lat,long,row.lat,row.long)
        distances.append(a)
# add the distance as a column to the DataFrame
    df['Distance'] = distances
    df = df.sort_values(['Distance'])
    df = df[df['Distance']<= miles]
# if showing only drive-thrus, filter the results before displaying the store list and the map
    if hasDriveThru == 'y':
        df = df.loc[df['Features - Stations'] == "Drive-Through"]
        if df.empty is True:
            print("Error. No stores are found \n")
            return
    else:
        df = df.loc[df['Features - Stations'] != "Drive-Through"]
        if df.empty is True:
            print("Error. No stores are found \n")
            return
    # if no stores are found, print a message,

    # otherwise print the list and the map
    dfDisplay(df)
    displayMap(df)


def findStoresWithinDistanceZip(dfStores):
    search = SearchEngine()
    # convert zip code to lat/long, then the problem is identical to the function above
    miles = int(input("Search radius in miles: "))
    zip = str(input("Enter zip code: "))
    #find the latitude and longitude of the zipcode.
    try:
        lat,long = latlongbyzipsearch(zip)
        data = search.by_coordinates(lat,long,radius=miles,returns=0)
    except Exception:
        print("Error. Invalid Zipcode\n")
        return
    #find all zipcode within the radius
    #add them to a list
    ziplist = []
    for i in data:
        a = i.to_dict()
        ziplist.append(a["zipcode"])
    df = dfStores[dfStores["Zip"].str.contains("|".join(ziplist),na=False)].copy()
# calculate the distance from each store to the home city/state,
    distances = []
    for row in df.iterrows():
        row = Store(row)
        a = distanceBetweenLocations(lat,long,row.lat,row.long)
        distances.append(a)
# add the distance as a column to the DataFrame
    df['Distance'] = distances
    df = df.sort_values(['Distance'])
    df = df[df['Distance']<= miles]
    dfDisplay(df)
    print()
    displayMap(df)



def main():

    dfStores = getData()
    MENU = """*** Starbucks Store Finder ***
    1 - Find Stores by City and State
    2 - Find Stores within Distance of City and State
    3 - Find Stores within Distance of Zip Code
    4 - Quit"""


    while True:
        print(MENU)
        choice = int(input("Enter your choice: "))
        if choice == 1:
            findStoresByCityState(dfStores)
        elif choice == 2:
            findStoresWithinDistanceCityState(dfStores)
        elif choice == 3:
            findStoresWithinDistanceZip(dfStores)
        elif choice == 4:
            print("Thank you for using the Store Finder App")
            break
        else:
            print("Error. Try again.")

if __name__ == "__main__":
    main()
