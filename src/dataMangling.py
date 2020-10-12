#!/usr/bin/env python3
"""
@summary: input data --> output data, misc helper functions

@version: v03.4 (24/June/2020)
@since:   26/April/2020

@author:  Dr Andreas Krueger
@see:     https://github.com/covh/covviz for updates

@param  AGS = https://de.wikipedia.org/wiki/Amtlicher_Gemeindeschl%C3%BCssel like riskLayer used it (4-5 digits)

@status:  Messy. Needs: (cleanup, function comments, solve TODOs, etc.)
          PERHAPS take apart, into several separate files?
          NOT yet: pretty, not at all easy to read, sorry. But it works.
"""

import os, copy
import datetime as dt
import pandas, numpy, matplotlib
import dataFiles


def find_AGS(ts, name):
    cond = ts['ADMIN'].str.contains(name, na=False)
    # return cond
    rows = ts.loc[cond]
    return rows

def to_dt(dt_str):
    d = list(map(int, dt_str.split(".")))
    # print(d)
    return dt.datetime(d[2], d[1], d[0])

def dates_list(ts):
    """
    extract the table headings = dates, in German formatting.
    """
    dates=[to_dt(d) for d in ts.columns[2:].values]
    # print (dates)
    # ts.values[0]
    return dates

def AGS_to_ts_total(ts, AGS):
    """
    please instead see below and use
    AGS_to_cumulative(ts_rich, datacolumns, AGS)
    """
    AGS = ("00000"+AGS)[-5:]
    row = ts.loc[ts['AGS'] == AGS]
    return row.values[0][2:].tolist()


def AGS_to_ts_daily(ts, AGS):
    """
    please instead see below and use
    AGS_to_daily(ts_rich, datacolumns, AGS)
    """
    AGS = ("00000"+AGS)[-5:]
    row = ts.loc[ts['AGS'] == AGS]

    # TODO: Use 'datacolumns' instead of dropping
    # print (row.drop(['AGS', 'ADMIN'], axis=1).columns); exit()
    row = row.drop(['AGS', 'ADMIN'], axis=1)
    # print(row.values); exit()
    # return row
    diff = row.diff(axis=1)
    return diff.values[0].tolist()


def AGS_to_population(bnn, AGS):
    # AGS = ("00000"+AGS)[-5:]
    AGS = int(AGS)
    # print(AGS)
    try:
        row = bnn.loc[bnn['AGS'] == AGS]
        pop = row["Population"].values[0]
        inf = row["Infections"].values[0]
        gen = row["GEN"].values[0]
        bez = row["BEZ"].values[0]
    except IndexError as e:
        # e.g. 11006 Zehlendorf does not exist in 'GermanyKreisebene_Risklayer_bnn-20200425.csv'
        print(f"error for {AGS=}, not found in BNN file")
        raise e from e
    return gen, bez, inf, pop

abbrev = {'Kreis': 'KR',
          'Kreisfreie Stadt' : 'KS',
          'Landkreis' : 'LK',
          'Stadtkreis': 'SK'}

def AGS_to_name_and_type(bnn, AGS):
    gen, bez, inf, pop = AGS_to_population(bnn, AGS)
    return "%s_%s" % (gen, abbrev[bez])


def AGS_to_Bundesland(bnn, AGS):
    # AGS = ("00000"+AGS)[-5:]
    AGS = int(AGS)
    row = bnn.loc[bnn['AGS'] == AGS]
    name = row["Bundesland"].values[0]
    inf_BL = row["Infections_Bundesland"].values[0]
    pop_BL = row["Population_Bundesland"].values[0]
    return name, inf_BL, pop_BL


def temporal_center(data):
    """
    find 'center' index of data by
    multiplying height with index, and test_Reff(ts_sorted, datacolumns)dividing by sum of heights

    TODO: what to do with the negative values?
          Cut them out before summing perhaps?
          On the other hand, they (temporarily-)LOCALLY correct over-reported cases, right?
          So perhaps better to leave them in?
    """
    ddata = data[1:] # drop the nan in the first cell, i.e. shift left
    # print (ddata)
    productsum = sum([d*(i+1) for i,d in enumerate(ddata)]) # add one i.e. shift right
    center = productsum/sum(ddata) # + 1 - 1 # shift left and right equalize each other
    # synthetic "data" with one peak near center:
    signal = [0]*len(data)

    # TODO: this could also be a signal that the source data is errorenous.
    #       perhaps let it fail instead of this workaround to keep going?
    if center < 0:
        print ("ALERT: centerday index negative = %.2f" % center)
        center = 0
    if int(round(center)) > len(data)-1:
        print ("ALERT: int(round(centerday)) index larger than array length = %.2f" % center)
        center = len(data)-1

    signal[int(round(center))]=max(ddata)*0.25
    return center, signal


def get_Kreise_max_prevalence_100k(bnn):
    max_prevalence_100k = bnn[bnn.columns[5]].str.replace(',', '.').astype(float).max() * 100
    return max_prevalence_100k


def get_Kreis(ts, bnn, AGS):
    # get data and names
    gen, bez, inf, pop = AGS_to_population(bnn, AGS)
    name_BL, inf_BL, pop_BL = AGS_to_Bundesland(bnn, AGS)
    title = "{} ({}, #{}, {}), Population={:,}".format(gen, bez, AGS, name_BL, pop)
    filename = "Kreis_" + ("00000"+AGS)[-5:] + ".png"
    daily = AGS_to_ts_daily(ts, AGS)
    cumulative = AGS_to_ts_total(ts, AGS)
    return daily, cumulative, title, filename, pop


def join_tables_for_and_aggregate_Bundeslaender(ts, bnn):

    # careful, there might be more fields with nan (currently just the 3 copyright rows)
    ts_int = copy.deepcopy(ts.dropna())

    ts_int["AGS"]=pandas.to_numeric(ts_int["AGS"]) # must transform string to int, for merge:
    ts_BuLa = pandas.merge(ts_int, bnn[["AGS", "Bundesland", "Population"]], how="left", on=["AGS"])

    Bundeslaender=ts_BuLa.drop(["AGS"], axis=1).groupby(["Bundesland"]).sum()
    print("consistency check, does this look like Germany's population? ", Bundeslaender["Population"].sum())

    Bundeslaender.loc['Deutschland'] = Bundeslaender.sum().astype('int32').values.tolist()

    return ts_BuLa, Bundeslaender


def get_BuLa(Bundeslaender, name, datacolumns):
    # get data and names
    filename = "bundesland_" + name + ".png"
    population = Bundeslaender.loc[name, "Population"]
    # row = Bundeslaender.loc[Bundeslaender['Bundesland'] == name]

    row = Bundeslaender[datacolumns].loc[[name]]

    cumulative=row.values[0].tolist()
    diff = row.diff(axis=1)
    daily = diff.values[0].tolist()

    title = name + " Population={:,}".format( population)

    return daily, cumulative, title, filename, population



def add_centerday_column(ts, ts_BuLa):

    ts_BuLa["centerday"] = [ temporal_center( AGS_to_ts_daily(ts, "%s" % AGS) )[0]
                            for AGS in ts_BuLa["AGS"].tolist() ]
    ts_sorted = ts_BuLa.sort_values("centerday", ascending=False).set_index("AGS")

    return ts_sorted

def add_centerday_column_Bundeslaender(Bundeslaender, datacolumns):
    Bundeslaender["centerday"] = [temporal_center(get_BuLa(Bundeslaender, name, datacolumns)[0])[0]
                                  for name in Bundeslaender.index.tolist() ]
    Bundeslaender.sort_values("centerday", ascending=False, inplace=True)
    return Bundeslaender


def maxdata(ts_sorted):
    maxvalue = max(ts_sorted[ts.columns[2:]].max())
    digits=int(1 + numpy.log10(maxvalue))
    return maxvalue, digits



def AGS_to_cumulative(ts_rich, datacolumns, AGS):
    """
    now also accepts tables with additional columns
    because positive selection by datacolumns (not negative by dropping columns)
    """
    # print (ts_rich)
    # AGS = ("00000%s"%AGS)[-5:]
    # row = ts.loc[ts['AGS'] == AGS]
    # return row[datacolumns].values[0].tolist()
    return ts_rich.loc[AGS][datacolumns].tolist()


def AGS_to_daily(ts_rich, datacolumns, AGS):
    """
    now also accepts tables with additional columns
    because positive selection by datacolumns (not negative by droppping columns)
    """
    cum = pandas.Series ( AGS_to_cumulative(ts_rich, datacolumns, AGS) )
    diff = cum.diff()
    return diff.values.tolist()

def cumulative_smoothed_last_week_incidence(cumulative, windowsize=7, daysBack=7):
    """
    experimental, not used yet
    'smoothed 1 week incidence'
    first averaging: 7 days rolling window, NOT centered, so that we have a result for today too
    then diff: look back 7 days
    """
    averaged=pandas.DataFrame(cumulative).rolling(window=windowsize, center=False).mean()[0].values.tolist()
    return averaged[-1] - averaged[-daysBack-1]


def cumulative_today_minus_last_week_smoothed(cumulative, windowsize=7, daysBack=7):
    """
    'one week incidence smoothed'
    step 1: averaging with 7 days rolling window, AND centered!
    step 2: today's (UNSMOOTHED) value minus the SMOOTHED value 1 week ago
    """
    averaged=pandas.DataFrame(cumulative).rolling(window=windowsize, center=True).mean()[0].values.tolist()
    return cumulative[-1] - averaged[-daysBack-1]


def multiDayNewCases(cumulative, daysBack=7):
    """
    unaveraged, will probably work best for daysBack=7 or 14 or 21
    """
    newCases = cumulative[-1] - cumulative[-daysBack-1]
    return newCases


def add_weekly_columns(ts_rich, datacolumns):

    for days in (14, 7):
        ts_rich["new_last%ddays" % days] = [multiDayNewCases( AGS_to_cumulative(ts_rich, datacolumns, AGS), days)
                                           for AGS in ts_rich.index.values.tolist() ]
    return ts_rich


def BL_to_cumulative(Bundeslaender_rich, datacolumns, BL_name):
    """
    now also accepts tables with additional columns
    because positive selection by datacolumns (not negative by dropping columns)
    """
    return Bundeslaender_rich.loc[BL_name][datacolumns].tolist()

def BL_to_daily(Bundeslaender_rich, datacolumns, BL_name):
    """
    can perhaps be replaced by AGS_to_daily because identical structure?
    """
    cum = pandas.Series ( BL_to_cumulative(Bundeslaender_rich, datacolumns, BL_name) )
    diff = cum.diff()
    return diff.values.tolist()



def add_weekly_columns_Bundeslaender(Bundeslaender, datacolumns):

    for days in (14, 7):
        colname = "new_last%ddays" % days
        Bundeslaender[colname] = [ multiDayNewCases(  BL_to_cumulative(Bundeslaender, datacolumns, name) , days)
                                  for name in Bundeslaender.index.tolist() ]

    return Bundeslaender


def Reff_4_4(daily,i):
    if i<7:
        return numpy.nan
    d=daily
    denominator = d[i-4]+d[i-5]+d[i-6]+d[i-7]
    result = (d[i]+d[i-1]+d[i-2]+d[i-3]) / denominator if denominator else numpy.nan
    return result


def Reff_4_7(dailyNewCases, i=None):
    """
    Quotient of day (i) and day (i-4)

    but working on smoothed daily cases, with window length = 7 days.
     ( simple moving average, not centered around i, but all days up to i )

    If i is not given, assume i to be the very last day in the time series.
     ( corresponds to 3 days ago compared with 7 days ago, in 'centered' moving average)

    see https://heise.de/-4712676 for explanations
    """
    if not i:
        i=len(dailyNewCases)-1
    if i<10:
        return numpy.nan
    #                               # clip away negative values:
    d=pandas.DataFrame(dailyNewCases).clip(lower=0)[0].values.tolist()
    # print ("daily only positives:", d)

    avg_gen_size_now  =   ( d[i]  +d[i-1]+d[i-2]+d[i-3]+d[i-4]+d[i-5]+d[i-6] ) / 7.0
    avg_gen_size_before = ( d[i-4]+d[i-5]+d[i-6]+d[i-7]+d[i-8]+d[i-9]+d[i-10]) / 7.0
    Reff = avg_gen_size_now / avg_gen_size_before if avg_gen_size_before else numpy.nan
    return Reff


def Reff_7_4(cumulative, i=None):
    """
    Quotient of weekly differences of totals ( x(i)-x(i-7) ) and ( x(i-7)-x(i-14) ).
    Then raised to the power 4/7, to transform the 7 days into 4 days generation time.
    """
    if not i:
        i=len(cumulative)-1
    if i<14:
        return numpy.nan
    c=cumulative

    avg_gen_size_now  =   ( c[i] -  c[i-7] )
    avg_gen_size_before = ( c[i-7]-c[i-14] )
    Reff = (avg_gen_size_now / avg_gen_size_before)**(4/7) if avg_gen_size_before else numpy.nan
    return Reff




def Reff_comparison(daily, cumulative, title, filename=None):
    daily_SMA=pandas.DataFrame(daily).rolling(window=7, center=True).mean()[0].values.tolist()
    daily_SMA
    # list(zip(cumulative,daily, daily_SMA))

    R1=[Reff_4_4(daily, i) for i, _ in enumerate(daily)]
    R2=[Reff_4_7(daily, i) for i, _ in enumerate(daily)]
    R3=[Reff_4_4(daily_SMA, i) for i, _ in enumerate(daily_SMA)]
    R4=[Reff_7_4(cumulative, i) for i, _ in enumerate(cumulative)]

    from matplotlib import pyplot as plt
    # matplotlib.pyplot.plot(R1)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(R1, label="Reff_4_4")
    ax.plot(R2, label="Reff_4_7")
    ax.plot(R3, label="Reff_4_4 on 7day-centered-SMA")
    ax.plot(R4, label="Reff_7_4")
    ax.legend()
    plt.title(title)

    if not filename:
        plt.show()
    else:
        fig.savefig(os.path.join(dataFiles.PICS_PATH, "R_experiments_" + filename),  bbox_inches='tight')

    print (Reff_4_7(daily), list(reversed(R2)))


def test_Reff_Kreis(ts_sorted, datacolumns):
    AGS=9377
    AGS=9479
    AGS=16076
    AGS=1061
    BL="Niedersachsen"
    print ("\nAGS")
    cumulative=ts_sorted.loc[AGS][datacolumns].tolist()
    print (list(reversed(cumulative)))
    # daily=ts_sorted.loc[AGS][datacolumns].diff().clip(lower=0).tolist()
    daily=ts_sorted.loc[AGS][datacolumns].diff().tolist()
    print (list(reversed(daily)))
    Reff_comparison(daily)

def test_Reff_BL(Bundeslaender, datacolumns, BL, filename=None):
    # BL="Niedersachsen"
    cumulative=Bundeslaender.loc[BL][datacolumns]
    daily=Bundeslaender.loc[BL][datacolumns].diff().tolist()
    Reff_comparison(daily, cumulative, title=BL, filename=filename)

def add_column_Kreise(ts_rich, datacolumns, inputseries=AGS_to_daily, operatorname="Reff_4_7_last", operator=Reff_4_7):

    ts_rich[operatorname] = [operator( inputseries(ts_rich, datacolumns, AGS) )
                             for AGS in ts_rich.index.values.tolist() ]
    return ts_rich


def add_column_Bundeslaender(Bundeslaender, datacolumns, inputseries=BL_to_daily, operatorname="Reff_4_7_last", operator=Reff_4_7):
    """
    can perhaps be replaced by add_column_Kreise because identical structure?
    """
    Bundeslaender[operatorname] = [ operator(  inputseries(Bundeslaender, datacolumns, name))
                                   for name in Bundeslaender.index.tolist() ]
    return Bundeslaender


def test_some_mangling():
    ts, bnn = dataFiles.data(withSynthetic=True)

    print (find_AGS(ts, "Osnabrück"))
    print (find_AGS(ts, "Heinsberg"))

    dates = dates_list(ts)

    AGS = "0"
    AGS = "1001"
    AGS = "5370"
    AGS = "9377"

    print ("AGS=%s" % AGS)
    print(AGS_to_ts_total(ts, AGS))
    print(AGS_to_ts_daily(ts, AGS))

    gen, bez, inf, pop = AGS_to_population(bnn, AGS)
    print (gen, bez, inf, pop)
    name, inf_BL, pop_BL = AGS_to_Bundesland(bnn, AGS)
    print (name, inf_BL, pop_BL )
    nameAndType = AGS_to_name_and_type(bnn, AGS)
    print (nameAndType )

    dailyIncrease = AGS_to_ts_daily(ts, "0")
    print (len(dailyIncrease))
    dailyIncrease = AGS_to_ts_daily(ts, "00000")
    print (len(dailyIncrease))

    center, signal = temporal_center(dailyIncrease)
    print ("expectation value at day %.2f" % center)
    # exit()

    print ("\nKreis")
    daily, cumulative, title, filename, pop = get_Kreis(ts, bnn, AGS)
    print (daily, cumulative)
    print (title, filename, pop)

    print ("\nBundesländer")
    ts_BuLa, Bundeslaender = join_tables_for_and_aggregate_Bundeslaender(ts, bnn)

    ts, bnn, ts_sorted, Bundeslaender_sorted, dates, datacolumns = dataMangled(withSynthetic=True)

    daily, cumulative, title, filename, population = get_BuLa(Bundeslaender, "Hessen", datacolumns)
    print (daily, cumulative)
    print (title, filename, population)

    # print ( maxdata(ts_sorted) )
    # total_max_cum, digits = maxdata(ts_sorted)

    AGS = 0
    AGS=1001
    AGS=5370
    print (AGS_to_cumulative(ts_rich=ts_sorted, datacolumns=datacolumns, AGS=AGS))
    print (AGS_to_daily(ts_rich=ts_sorted, datacolumns=datacolumns, AGS=AGS))

    cumulative=AGS_to_cumulative(ts_rich=ts_sorted, datacolumns=datacolumns, AGS=AGS)
    print (cumulative_smoothed_last_week_incidence(cumulative))
    print (cumulative_today_minus_last_week_smoothed(cumulative))
    print (multiDayNewCases(cumulative))
    print (multiDayNewCases(cumulative, 14))
    print (multiDayNewCases( AGS_to_cumulative(ts_sorted, datacolumns, AGS) , 14) )
    print (ts_sorted.loc[AGS][["new_last14days", "new_last7days"]]); # exit()
    print (ts_sorted["new_last14days"][AGS]);

    # print (add_weekly_columns_Bundeslaender(Bundeslaender_sorted, datacolumns))
    print (add_weekly_columns_Bundeslaender(Bundeslaender_sorted, datacolumns)[["new_last14days", "new_last7days"]])

    # test_Reff_Kreis(ts_sorted, datacolumns)
    # test_Reff_BL(Bundeslaender_sorted, datacolumns, BL="Hamburg")

    for BL in Bundeslaender_sorted.index:
        test_Reff_BL(Bundeslaender_sorted, datacolumns, BL=BL, filename=BL+".png")


def additionalColumns(ts,bnn):
    """
    this can operate on data in RAM
    """
    dates = dates_list(ts)
    datacolumns = ts.columns[2:]
    print ("\nNewest column = '%s'" % datacolumns[-1])
    ts_BuLa, Bundeslaender = join_tables_for_and_aggregate_Bundeslaender(ts, bnn)
    ts_sorted = add_centerday_column(ts, ts_BuLa)
    ts_sorted = add_weekly_columns(ts_sorted, datacolumns)
    ts_sorted = add_column_Kreise(ts_sorted, datacolumns, inputseries=AGS_to_daily, operatorname="Reff_4_7_last", operator=Reff_4_7)
    Bundeslaender_sorted = add_centerday_column_Bundeslaender(Bundeslaender, datacolumns)
    Bundeslaender_sorted = add_weekly_columns_Bundeslaender(Bundeslaender_sorted, datacolumns)
    Bundeslaender_sorted = add_column_Bundeslaender(Bundeslaender_sorted , datacolumns, inputseries=BL_to_daily, operatorname="Reff_4_7_last", operator=Reff_4_7)
    return  ts, bnn, ts_sorted, Bundeslaender_sorted, dates, datacolumns

def dataMangled(withSynthetic=True, ifPrint=True):
    """
    this loads from disk first
    """
    ts, bnn = dataFiles.data(withSynthetic=withSynthetic, ifPrint=ifPrint)

    ts, bnn, ts_sorted, Bundeslaender_sorted, dates, datacolumns = additionalColumns(ts,bnn)

    return ts, bnn, ts_sorted, Bundeslaender_sorted, dates, datacolumns



if __name__ == '__main__':
    test_some_mangling(); exit()

    # ts, bnn, ts_sorted, Bundeslaender_sorted, dates, datacolumns = dataMangled(withSynthetic=True)

