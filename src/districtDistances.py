#!/usr/bin/env python3
"""
@summary: Opendatasoft database into pairwise distances of all districts of Germany

@version: v03.5.2 (9/Sept/2020)
@since:   27/April/2020

@author:  Dr Andreas Krueger
@see:     https://github.com/covh/covviz for updates

@status:  needs: (cleanup, function comments, solve/record TODOs, declutter main() function, etc.)
          not yet: ready, clearly structured, pretty. But ... it works.


@output: example

whole table contains 1870 pairs with distance max 50.0 km
example for AGS1= 9362
      AGS1  AGS2         km
0     9362  9375   1.067573
954   9362  9273  28.111665
1940  9362  9278  36.566027
1961  9362  9263  36.750851
2514  9362  9376  40.761417
3162  9362  9373  45.877283
3636  9362  9372  49.228091



@note:    how to run this, quickstart:

git clone https://github.com/covh/covviz.git
cd covviz

sudo apt install git python3-venv expect
python3 -m venv ./py3science

source ./py3science/bin/activate
pip3 install -U pip wheel
pip install -r requirements.txt

cd src
python3 districtDistances.py

# in first run, change to GENERATE_NEW = True
"""

####################

GENERATE_NEW = False # If you set this to True, the pairwise calculations will need time. Switch back to False afterwards.

####################


import io, sys, shutil

import pandas
import requests
import geopy.distance
import wget

import dataMangling, dataFiles
from dataFiles import DATA_PATH, OPENDATASOFT_URL01, OPENDATASOFT_URL02, OPENDATASOFT_PATH, DISTANCES_PATH

CSV_FIELD_REGIONAL_CODE="Regional code"

def download_kreise_locations(url1=OPENDATASOFT_URL01, url2=OPENDATASOFT_URL02, out=OPENDATASOFT_PATH):
    print ("Downloading large table with Kreise locations. For infos see")
    print (url1)
    print ("Patience please ...", end=" ")
    try:
        shutil.move(out, out+".bak")
    except:
        pass
    filename = wget.download(url2, out=out)
    print ("Done -->", filename)
    return filename

def repair_kreise_locations(LKG):
    # Goettingen old=3152 new 3159
    i=LKG[LKG[CSV_FIELD_REGIONAL_CODE]==3152].index.tolist()
    if i:
        LKG.at[i, CSV_FIELD_REGIONAL_CODE] = 3159

    # Osterode old=3156, now part of 3159
    i=LKG[LKG[CSV_FIELD_REGIONAL_CODE]==3156].index.tolist()
    if i:
        LKG.drop(index=i, inplace=True)
    print ("Done repairing data (Osterode, Goettingen) --> Goettingen AGS 3159.")
    return LKG

def load_kreise_locations(filename = OPENDATASOFT_PATH):
    # s=requests.get(url2).content
    # LKG=pandas.read_csv(io.StringIO(s.decode('utf-8')), sep=';') # error_bad_lines=False)
    LKG=pandas.read_csv(filename, sep=';')
    # immediately drop non-Kreis row(s)
    LKG.dropna(subset=[CSV_FIELD_REGIONAL_CODE],inplace=True)
    # turn AGS into integer:
    LKG[CSV_FIELD_REGIONAL_CODE]=LKG[CSV_FIELD_REGIONAL_CODE].astype(int)
    print ("Done downloading.")
    LKG = repair_kreise_locations(LKG)

    return LKG

def accelerate_lookup(LKG):
    # accelerate lookup
    AGS_to_geopoint=dict(LKG[[CSV_FIELD_REGIONAL_CODE,"Geo Point"]].set_index(CSV_FIELD_REGIONAL_CODE).to_dict('series')["Geo Point"])
    print ("Done generating lookup dict")
    return AGS_to_geopoint


def geo_distance(AGS_to_geopoint, AGS1, AGS2):
    c1 = list(map(float,AGS_to_geopoint[AGS1].split(",")))
    c2 = list(map(float,AGS_to_geopoint[AGS2].split(",")))
    # print (c1, c2 )
    return geopy.distance.geodesic(c1, c2).kilometers


def make_distances_table(AGS_to_geopoint, all_AGS, filename=DISTANCES_PATH):
    headers = ['AGS1','AGS2','km']
    counter,countermax=0, len(all_AGS)*(len(all_AGS)-1)
    distances=pandas.DataFrame([], columns = headers)
    for AGS1 in all_AGS:
        for AGS2 in all_AGS:
            if AGS1>=AGS2:
                continue
            geodist = geo_distance(AGS_to_geopoint, AGS1, AGS2)
            row=pandas.Series([AGS1, AGS2, geodist], index=headers)
            distances=distances.append(row, ignore_index=True)
            row=pandas.Series([AGS2, AGS1, geodist], index=headers)
            distances=distances.append(row, ignore_index=True)
            counter+=2
            if not counter%500:
                print (counter, "/", countermax)

    print ("Done calculating distances. Len(table)=%d" % len(distances))

    distances["AGS1"]=distances["AGS1"].astype(int)
    distances["AGS2"]=distances["AGS2"].astype(int)

    print ("Distances are distributed like this:")
    print(distances["km"].describe())

    distances.sort_values("km", inplace=True)
    print("Done sorting.")

    distances.to_csv(filename, index=False)
    print ("Saved to", filename)
    return distances, filename

def load_distances(filename = DISTANCES_PATH):
    distances = pandas.read_csv(filename)
    return distances

def number_of_pairs_max_dist(distances, km):
    return len( distances[(distances.km<=km)] ) / 2

def nearby(distances, AGS, km):
    return distances[(distances.km<=km) & (distances.AGS1==AGS)]

def kreis_link(bnn, AGS):
    nameAndType = dataMangling.AGS_to_name_and_type(bnn, AGS)
    name_BL, inf_BL, pop_BL = dataMangling.AGS_to_Bundesland(bnn, AGS)
    AGS_5digits = ("00000%s" % AGS) [-5:]
    filename = "%s.html#AGS%s" % (name_BL, AGS_5digits)
    link='<a id="%s" href="%s">%s</a>' % (nameAndType, filename, nameAndType) # also give it an id, so sorting alphabetically works even though the filename starts with bundesland
    return filename, nameAndType, link

def kreis_nearby_links(bnn, distances, AGS, km=50):
    neighbours = nearby (distances, AGS, km)
    linklist=[]
    AGSlist=[]
    for AGS2 in neighbours["AGS2"].tolist():
        # print (AGS2)
        try:
            filename, nameAndType, link = kreis_link(bnn, AGS2)
            # print (filename, nameAndType)
            linklist.append(link)
            AGSlist.append(str(AGS2))
        except IndexError:
            print(f"{AGS2=} could not be linked, ignoring")
    return ", ".join(linklist), ",".join(AGSlist)


def compare_risklayer_with_opendatasoft(bnn):
    filename = dataFiles.OPENDATASOFT_PATH
    LKG = load_kreise_locations(filename)
    ODS = set(LKG[CSV_FIELD_REGIONAL_CODE].tolist())
    ts, bnn = dataFiles.data(withSynthetic=True)
    RSL=set(bnn["AGS"].values.tolist())

    diff1 = list(ODS-RSL)
    names1=([LKG["Name 2"][LKG[CSV_FIELD_REGIONAL_CODE]==AGS].tolist()[0] for AGS in diff1])
    print ("ODS-RSL: %s = %s"% (diff1, names1))
    diff2 = list(RSL-ODS)
    names2=([bnn["GEN"][bnn["AGS"]==AGS].tolist()[0] for AGS in diff2])
    print ("RSL-ODS: %s = %s"% (diff2, names2))


def downloadFromOpendatasoft_and_generatePairwiseDistancesFile():

    print ("\nWe want the neighbour districts. So first download the GPS midpoints and then calculate the pairwise distances, and sort them.\n")

    # filename = OPENDATASOFT_PATH
    filename = download_kreise_locations()

    LKG = load_kreise_locations(filename)

    AGS_to_geopoint = accelerate_lookup(LKG)
    print ("sample distance", geo_distance(AGS_to_geopoint, 1001, 1002))

    all_AGS=LKG[CSV_FIELD_REGIONAL_CODE].dropna().astype(int).tolist()
    # all_AGS=all_AGS[:40] # reduce number for dev'ing
    print("now pairwise distances for %d locations" % len(all_AGS))
    print()

    distances, filename = make_distances_table(AGS_to_geopoint, all_AGS)

    AGS1, km = all_AGS[0], 150
    print("testing with AGS=%d and km=%d:" % (AGS1, km))
    print (distances[(distances.km<km) & (distances.AGS1==AGS1)])

    return filename


if __name__ == '__main__':


    if GENERATE_NEW:
        downloadFromOpendatasoft_and_generatePairwiseDistancesFile()

    # ts, bnn, ts_sorted, Bundeslaender_sorted, dates, datacolumns = dataMangling.dataMangled()
    # print ("\ns**t that had been inconsistent data:")
    # compare_risklayer_with_opendatasoft(bnn)
    # print ("\nall good.")

    try:
        distances = load_distances()
    except Exception as e:
        print ("%s, first enable table file generation: GENERATE_NEW = True" % e)
    else:
        AGS1,km = distances["AGS1"][0], 50
        print ("\nwhole table contains %d pairs with distance max %.1f km" % (number_of_pairs_max_dist(distances, km), km))
        print ("example for AGS1=" , AGS1)
        print (nearby (distances, AGS1, km))

    #print()
    #print (kreis_link(bnn, 0))
    #print (kreis_link(bnn, 1001))
    # print (kreis_link(bnn, 3152))

    # print (districtDistances.nearby(distances, 1001, 50))
    #AGS=1001
    #print( kreis_nearby_links(bnn, distances, AGS, km=50) )

