#!/usr/bin/env python3
"""
@summary: plot timeseries of (cumulative, daily) number of confirmed cases

@version: v03.6.6 (03/Oct/2020)
@since:   25/April/2020

@author:  Dr Andreas Krueger
@see:     https://github.com/covh/covviz for updates

@status:  Needs: (cleanup, function comments, etc.)
          See: todo.md for ideas what else to do. 
          NOT yet: pretty. But it works.
"""

import datetime
import os

# import numpy
import matplotlib
import pandas

matplotlib.use('Agg')  # to be able to plot without GUI, this must be set before importing pyplot
from matplotlib import pyplot as plt

import dataFiles, dataMangling

weeklyIncidenceLimit1Per100k = 35
weeklyIncidenceLimit2Per100k = 50


def plot_timeseries(datacolumns, dates, daily, cumulative, title, filename, ifShow=True, ifCleanup=True, population=None):
    PLOT_YLIM_ENLARGER = 1.1
    fig, ax = plt.subplots(figsize=(10, 6))  # , constrained_layout=True)
    # plt.tight_layout()
    plt.grid(True, which='major', axis='x', ls='-', alpha=0.9)  # if not set here above, major ticks of x axis won't be visible
    plt.grid(True, which='minor', axis='x', ls='--', alpha=0.7)  # if not set here above, minor ticks of x axis won't be visible
    plt.grid(True, which='major', axis='y', ls='-', alpha=0.9)  # if not set here above, ticks of left side y axis won't be visible
    plt.grid(True, which='minor', axis='y', ls='--', alpha=0.7)

    # x axis
    ax.xaxis_date()
    fig.autofmt_xdate(rotation=60)
    ax.xaxis.set_minor_locator(matplotlib.dates.DayLocator(bymonthday=range(1, 30, 5)))

    # plot data
    y_max = max(daily[1:])
    plt.ylim(0, y_max * PLOT_YLIM_ENLARGER)
    lns1 = ax.plot(dates, daily, label="daily cases (weekend-flawed)", color='#AAAAAA')
    # lns1 = ax.plot(dates, daily, label="daily cases (weekend-flawed), 2 weeks: red", color='#AAAAAA')
    # lns1_2 = ax.plot(dates[-14:], daily[-14:], label="daily cases, last 14 days dark gray", color='red')
    # print (len(dates[-14:]))

    # allow no 'half daily cases' (floating point numbers)
    yloc = matplotlib.ticker.MaxNLocator(integer=True)
    ax.yaxis.set_major_locator(yloc)

    plt.ylabel("daily cases")
    y_max = max(daily[1:])
    plt.ylim(0, y_max * PLOT_YLIM_ENLARGER)

    lns0 = []
    rolling_sum_max = 0
    if population:
        # plot 7 day sums, only if incidence borders are available
        window = 7
        rolling_sum = pandas.DataFrame(daily).rolling(window=window, center=False).sum()
        lns0 = ax.plot(dates, rolling_sum, label='sum of daily cases of prior %s days for date' % window, color='red')
        rolling_sum_max = rolling_sum[0].max()
        y_max = max(y_max, rolling_sum_max)
        plt.ylim(0, y_max * PLOT_YLIM_ENLARGER)

    # plot averages
    window = 14
    rolling_mean = pandas.DataFrame(daily).rolling(window=window, center=True).mean()
    lns3 = ax.plot(dates, rolling_mean, label='daily: centered moving average %s days' % window, color='orange', linewidth=4)
    window = 7
    rolling_mean = pandas.DataFrame(daily).rolling(window=window, center=True).mean()
    lns2 = ax.plot(dates, rolling_mean, label='daily: centered moving average %s days' % window, color='purple')
    # window=21
    # rolling_mean = pandas.DataFrame(daily).rolling(window=window, center=True).mean()
    # ax.plot(dates, rolling_mean, label='SMA %s days' % window, color='pink', linewidth=1)

    lns6_1 = []
    lns6_2 = []
    if population:
        limit = weeklyIncidenceLimit1Per100k * population / 100000
        # print ("limit:", limit)
        lns6_1 = ax.plot([dates[0]] + [dates[-3]], [limit, limit], label="incid. border %i/week/100k pop.: %.2f" % (weeklyIncidenceLimit1Per100k, limit), color='#ff8c8c', linestyle=(0, (3, 5)))

        if rolling_sum_max > limit * 0.8:
            # plot second incidence border only if first one is nearly reached
            limit = weeklyIncidenceLimit2Per100k * population / 100000
            # print ("limit:", limit)
            lns6_2 = ax.plot([dates[0]] + [dates[-3]], [limit, limit], label="incid. border %i/week/100k pop.: %.2f" % (weeklyIncidenceLimit2Per100k, limit), color='#df4c4c', linestyle=(0, (5, 4)))

        y_max = max(y_max, limit)
        plt.ylim(0, y_max * PLOT_YLIM_ENLARGER)

    # determine some meaningfull y minor tick value -- again, should be placed below here, to get final good results
    yticks = yloc()
    ydiff = yticks[1]
    yminor = int(ydiff / 5 + 0.5) if ydiff >= 8 else 1  # '+0.5' to round up for '8'
    # print(f"{ydiff} results in {yminor} for {title} and {yticks=}")
    ax.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(yminor))

    # plot center bar
    center, signal = dataMangling.temporal_center(daily)
    # print (center)
    center_date = datacolumns.values[int(round(center))]
    # lns4 = ax.bar(dates, signal, label="'expectation day': "+center_date, color='green')

    # lns4_2 = plt.plot(dates[int(round(center))], max(signal), marker="v", color='green', markersize=15)
    # lns4_2 = plt.plot(dates[int(round(center))], 0, marker="v", color='green', markersize=15)
    # lns4_2 = plt.plot(dates[int(round(center))], [max(daily[1:])/20], marker="^", color='green', markersize=30)
    lns4_2 = plt.plot(dates[int(round(center))], [yminor * 1.3], marker="v", color='green', markersize=16)  # if markersize is an odd number, the triangle will be skewed

    # plot 2nd axis and cumulative data
    ax2 = plt.twinx()
    plt.ylim(0, max(cumulative) * 1.1)

    plt.ylabel("cumulative total cases", color="#1E90FF")

    lns5 = ax2.plot(dates, cumulative, label="total cases reported at RiskLayer", color='#1E90FF')

    lines = lns5 + lns0 + lns1 + lns2 + lns3 + lns6_1 + lns6_2
    labs = [l.get_label() for l in lines]

    text = "source data @RiskLayer up to " + ("%s" % max(dates))[:10]
    text += "\nplot @DrAndreasKruger (+contrib.) " + ("%s" % datetime.datetime.now())[:16]
    text += "\ndaily: (GREEN) 'expectation day' = " + center_date

    plt.legend(lines, labs, loc='upper left', facecolor="#fafafa", framealpha=0.6,
               title=text, prop={'size': 8}, title_fontsize=8)

    plt.title(title)

    ax.xaxis.set_major_locator(matplotlib.dates.DayLocator(bymonthday=range(1, 32, 31)))  # if placing this setting above all other, major ticks won't appear
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y-%m"))  # its date formatter must be set, if setting major locator

    if filename:
        fig.savefig(os.path.join(dataFiles.PICS_PATH, filename), bbox_inches='tight')

    if ifShow:
        plt.show()

    if ifCleanup:
        plt.clf()
        plt.close("all")

    return plt, fig, ax, ax2


def test_plot_Kreis(ts, bnn, dates, datacolumns):
    ## Kreis
    AGS = "0"
    # AGS = "1001"
    AGS = "5370"
    # AGS = "9377"
    daily, cumulative, title, filename, pop = dataMangling.get_Kreis(ts, bnn, AGS)
    plot_timeseries(datacolumns, dates, daily, cumulative, title, filename=filename, population=pop)


def plot_Kreise(ts, bnn, dates, datacolumns, Kreise_AGS, ifPrint=True):
    done = []
    for AGS in Kreise_AGS:
        daily, cumulative, title, filename, pop = dataMangling.get_Kreis(ts, bnn, AGS)
        plot_timeseries(datacolumns, dates, daily, cumulative, title, filename=filename, ifShow=False, population=pop)
        done.append((title, filename))
        if ifPrint:
            print(title, filename)
        else:
            print(".", end="")
            if len(done) % 60 == 0:
                print()
    if not ifPrint:
        print()
    return done


def plot_Kreise_parallel(ts, bnn, dates, datacolumns, Kreise_AGS, ifPrint=True):
    import multiprocessing as mp

    # one CPU should be left free for the system, and multiprocessing makes only sense for at least 2 free CPUs,
    # so just call the non-parallel version if not enough CPUs are in the system
    available_cpus = mp.cpu_count()
    leave_alone_cpus = 1
    wanted_cpus = available_cpus - leave_alone_cpus

    if available_cpus < wanted_cpus or wanted_cpus < 2:
        return plot_Kreise(ts, bnn, dates, datacolumns, Kreise_AGS, ifPrint)

    done = []

    # setup process pool
    pool = mp.Pool(wanted_cpus)
    try:
        done = pool.starmap(plot_Kreise, [(ts, bnn, dates, datacolumns, [AGS], ifPrint) for AGS in Kreise_AGS])
    except KeyboardInterrupt:
        # without catching this here we will never be able to manually stop running in a sane way
        pool.terminate()
    finally:
        pool.close()
        pool.join()

    return done


def test_plot_Bundesland(ts, bnn, dates, datacolumns, Bundesland="Hessen"):
    ## Bundesland
    # Bundesland = "Dummyland"

    ts_BuLa, Bundeslaender = dataMangling.join_tables_for_and_aggregate_Bundeslaender(ts, bnn)
    daily, cumulative, title, filename, population = dataMangling.get_BuLa(Bundeslaender, Bundesland, datacolumns)
    plot_timeseries(datacolumns, dates, daily, cumulative, title, filename=filename)


def plot_all_Bundeslaender(ts, bnn, dates, datacolumns, ifPrint=True):
    ts_BuLa, Bundeslaender = dataMangling.join_tables_for_and_aggregate_Bundeslaender(ts, bnn)
    filenames, population = [], 0
    done = []
    for BL in Bundeslaender.index.tolist():
        print(BL, end=" ")
        daily, cumulative, title, filename, pop_BL = dataMangling.get_BuLa(Bundeslaender, BL, datacolumns)
        if BL == "Deutschland":
            filename = filename.replace("bundesland_", "")
        plot_timeseries(datacolumns, dates, daily, cumulative, title, filename=filename, ifShow=False)
        filenames.append(filename)
        population += pop_BL
        if ifPrint:
            print(title, filename)
        done.append((title, filename))
    print("\nTotal population covered:", population)
    if ifPrint:
        print("%d filenames written: %s" % (len(filenames), filenames))
    return done


if __name__ == '__main__':

    # ts, bnn = dataFiles.data(withSynthetic=True)
    # dates = dataMangling.dates_list(ts)
    ts, bnn, ts_sorted, Bundeslaender_sorted, dates, datacolumns = dataMangling.dataMangled(withSynthetic=True)

    examples = True
    if examples:
        test_plot_Kreis(ts, bnn, dates, datacolumns)
        test_plot_Bundesland(ts, bnn, dates, datacolumns)
        test_plot_Bundesland(ts, bnn, dates, datacolumns, Bundesland="Deutschland")

    longrunner = True
    if longrunner:
        plot_Kreise(ts, bnn, dates, datacolumns, ts["AGS"].tolist())
        plot_all_Bundeslaender(ts, bnn, dates, datacolumns)
