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
    """Creates the image with the different statistic graph plots for the covid-19 cases of a country, Bundesland or Kreis"""
    from matplotlib.offsetbox import AnchoredOffsetbox, TextArea, VPacker

    PLOT_YLIM_ENLARGER = 1.1
    COLOR_INC_SUM = '#000060'
    fig, ax = plt.subplots(figsize=(10, 6))  # , constrained_layout=True)
    
    ax2 = ax.twinx()
    ax_sum = ax.twinx()
    
    # plt.tight_layout()

    # set grids
    ax.grid(True, which='major', axis='x', ls='-', alpha=0.9)  # if not set here above, major ticks of x axis won't be visible
    ax.grid(True, which='minor', axis='x', ls='--', alpha=0.5)  # if not set here above, minor ticks of x axis won't be visible
    #ax.grid(True, which='major', axis='y', ls='-', alpha=0.7)  # if not set here above, ticks of left side y axis won't be visible
    #ax.grid(True, which='minor', axis='y', ls='--', alpha=0.5)

    # set x axis minor tick interval to only each 5 days one tick, as compromise between being exact and easily readable
    fig.autofmt_xdate(rotation=60)
    ax.xaxis_date()
    ax.xaxis.set_minor_locator(matplotlib.dates.DayLocator(bymonthday=range(1, 30, 5)))


    # plot raw daily cases
    lns1 = ax.plot(dates, daily, label="raw daily cases (weekend-flawed)", color='#999999')
    # lns1 = ax.plot(dates, daily, label="daily cases (weekend-flawed), 2 weeks: red", color='#AAAAAA')
    # lns1_2 = ax.plot(dates[-14:], daily[-14:], label="daily cases, last 14 days dark gray", color='red')
    # print (len(dates[-14:]))

    # set y1 axis tick automatic interval and range restrictions, allow no 'half daily cases' (no floating point numbers)
    yloc = matplotlib.ticker.MaxNLocator(integer=True)
    ax.yaxis.set_major_locator(yloc)
    ax.set_ylim(0, max(daily[1:]) * PLOT_YLIM_ENLARGER)

    #  plot rolling averages for daily cases
    window = 14
    rolling_mean = pandas.DataFrame(daily).rolling(window=window, center=True).mean()
    lns3 = ax.plot(dates, rolling_mean, label="centered moving average, %s days cases" % window, color='orange', linewidth=4)
    lns2 = []
    # window = 7
    # rolling_mean = pandas.DataFrame(daily).rolling(window=window, center=True).mean()
    # lns2 = ax.plot(dates, rolling_mean, label="centered moving average, %s days' cases" % window, color='#900090')
    # window=21
    # rolling_mean = pandas.DataFrame(daily).rolling(window=window, center=True).mean()
    # ax.plot(dates, rolling_mean, label='SMA %s days' % window, color='pink', linewidth=1)

    # y-axis label multi colored
    ybox1 = TextArea("raw daily cases", textprops=dict(color=lns1[0].get_color(), rotation='vertical'))
    ybox2 = TextArea(" / ", textprops=dict(color="black", rotation='vertical'))
    ybox3 = TextArea("moving average", textprops=dict(color=lns3[0].get_color(), rotation='vertical'))
    ybox = VPacker(children=[ybox3, ybox2, ybox1], align="center", pad=0, sep=5)
    anchored_ybox = AnchoredOffsetbox(loc=8, child=ybox, pad=0., frameon=False,
                                      bbox_to_anchor=(-0.06, 0.2),
                                      bbox_transform=ax.transAxes, borderpad=0.)
    ax.add_artist(anchored_ybox)


    # plot rolling sum of prior 7 days cases for date
    rolling_sum_max = 0
    lns0 = []
    lns6_1 = []
    lns6_2 = []
    if population:
        ax_sum.grid(True, which='major', axis='y', ls='-', alpha=0.6, color=COLOR_INC_SUM)  # if not set here above, ticks of left side y axis won't be visible
        ax_sum.grid(True, which='minor', axis='y', ls='--', alpha=0.1, color=COLOR_INC_SUM)
        
        # move total cases y axis to outside
        ax2.spines["right"].set_position(("axes", 1.15))
        yloc2 = matplotlib.ticker.MaxNLocator(integer=True)
        ax_sum.yaxis.set_major_locator(yloc2)

        # plot 7 day sums, only if incidence borders are available
        window = 7
        label = 'sum of daily cases, for prior %s days of date' % window
        rolling_sum = pandas.DataFrame(daily).rolling(window=window, center=False).sum()
        # plot yellow background
        lns0 = ax_sum.plot(dates, rolling_sum, label=label, color='yellow', linewidth=7, alpha=0.4)
        lns0 = ax_sum.plot(dates, rolling_sum, label=label, color=COLOR_INC_SUM)
        rolling_sum_max = rolling_sum[0].max()
        
        # set axis properties
        ax_sum.set_ylim(0, rolling_sum_max * PLOT_YLIM_ENLARGER)
        # also yellow background for label
        ax_sum.set_ylabel(label + "\n(to determine incidence borders)", color=COLOR_INC_SUM, 
                          bbox=dict(color='yellow', alpha=0.3, boxstyle='round', mutation_aspect=0.5))
        ax_sum.tick_params(axis='y', colors=COLOR_INC_SUM, size=4, width=1.5)
        
        # adjust axis visibility
        ax_sum.set_frame_on(True)
        ax_sum.patch.set_visible(False)
        for sp in ax_sum.spines.values():
            sp.set_visible(False)
        ax_sum.spines["right"].set_visible(True)
        
        
        yticks = yloc2()
        ydiff = yticks[1]
        yminor = int(ydiff / 5 ) if ydiff >= 8 else 1  
        # print(f"{ydiff} results in {yminor} for {title} and {yticks=}")
        ax_sum.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(yminor))


    
        # plot incidence border lines
        limit = weeklyIncidenceLimit1Per100k * population / 100000
        # print ("limit:", limit)
        lns6_1 = ax_sum.plot([dates[40]] + [dates[-1]], [limit, limit], label="incid. border %i/week/100k pop.: %.2f" % (weeklyIncidenceLimit1Per100k, limit), color='#ff8c8c', linestyle=(0, (3, 5)))

        # plot second incidence border only if first one is nearly reached, to have no unneeded large y1 numbers which would worsen the view
        if rolling_sum_max > limit * 0.8:
            limit = weeklyIncidenceLimit2Per100k * population / 100000
            # print ("limit:", limit)
            lns6_2 = ax_sum.plot([dates[40]] + [dates[-1]], [limit, limit], label="incid. border %i/week/100k pop.: %.2f" % (weeklyIncidenceLimit2Per100k, limit), color='#df4c4c', linestyle=(0, (5, 4)))
        ax_sum.set_ylim(0, max(rolling_sum_max, limit) * PLOT_YLIM_ENLARGER)
        
        # set new ax limit for daily cases / averaging, trying to have evenly distributed major ticks for both
        
        #yticks_daily = len(yloc())
        #yticks_sum = len(yloc2())
        #ystep_daily = 0
        #if (tick_diff := yticks_sum - yticks_daily) > 0:
        #    ystep_daily = yloc()[1]
        #    ax.set_ylim(0, ystep_daily * yticks_sum * PLOT_YLIM_ENLARGER)
        #print(yticks_daily, yticks_sum, tick_diff, ystep_daily, ystep_daily * yticks_sum * PLOT_YLIM_ENLARGER)
        #print(yloc(), yloc2())
        ax.set_ylim(0, yloc()[-2])
        ax_sum.set_ylim(0, yloc2()[-2])
        yticks = yloc2()
        ydiff = yticks[1]
        yminor = int(ydiff / 5 + 0.5) if ydiff >= 8 else 1  # '+0.5' to round up for '8'
        # print(f"{ydiff} results in {yminor} for {title} and {yticks=}")
        ax_sum.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(yminor))
        

    if not population:
        ax.grid(True, which='major', axis='y', ls='-', alpha=0.9)  # if not set here above, ticks of left side y axis won't be visible
        ax.grid(True, which='minor', axis='y', ls='--', alpha=0.7)
        # determine some meaningfull y1 minor tick value, also used for setting center bar's y position
        yticks = yloc()
        ydiff = yticks[1]
        yminor = int(ydiff / 5 + 0.5) if ydiff >= 8 else 1  # '+0.5' to round up for '8'
        # print(f"{ydiff} results in {yminor} for {title} and {yticks=}")
        ax.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(yminor))


    # plot temporal center date marker
    center, signal = dataMangling.temporal_center(daily)
    center_date = datacolumns.values[int(round(center))]
    # print (center)
    # lns4 = ax.bar(dates, signal, label="'expectation day': "+center_date, color='green')
    # lns4_2 = plt.plot(dates[int(round(center))], max(signal), marker="v", color='green', markersize=15)
    # lns4_2 = plt.plot(dates[int(round(center))], 0, marker="v", color='green', markersize=15)
    # lns4_2 = plt.plot(dates[int(round(center))], [max(daily[1:])/20], marker="^", color='green', markersize=30)

    # the '1.3'-multiplier below, for setting the y-position of the marker, is a none-deterministic evaluated value which lets the
    #   triangle marker's bottom point be placed nearly at the x-axis, for all of the 400+ Kreise with their different case numbers
    # (dummy marker just for later showing in legend with smaller symbol, gets plotted over with 2nd one)
    lns4_1 = plt.plot(dates[int(round(center))], [yminor * 1.3], marker="v", color='green', markersize=8, label="marker for 'expectation day': "+center_date, linestyle="")  # if markersize is an odd number, the triangle will be skewed
    # (side note: if markersize here would be an odd number, the triangle would be skewed)
    lns4_2 = plt.plot(dates[int(round(center))], [yminor * 1.3], marker="v", color='green', markersize=16)


    # plot cumulative cases data for the 2nd y axis
    lns5 = ax2.plot(dates, cumulative, label="total cases reported at RiskLayer", color='#1E90FF', 
                    linestyle='dotted', linewidth=2)
    ax2.set_ylim(0, max(cumulative) * PLOT_YLIM_ENLARGER)
    ax2.set_ylabel("cumulative total cases")
    ax2.yaxis.label.set_color(color=lns5[0].get_color())
    ax2.tick_params(axis='y', colors=lns5[0].get_color())

        
    # build legend
    # collect lines which shall get a label in legend
    lines = lns4_1 + lns5 + lns0 + lns1 + lns2 + lns3  + lns6_2 + lns6_1
    labs = [l.get_label() for l in lines]

    # text for legend
    text = "source data: ©RiskLayer up to " + ("%s" % max(dates))[:10]
    text += " – plot:\n©DrAndreasKruger (+contrib.) " + ("%s" % datetime.datetime.now())[:16]
    # text += "\ndaily: (GREEN) 'expectation day' = " + center_date

    # plot legend and title
    plt.legend(lines, labs, loc='upper left', facecolor="#fafafa", framealpha=0.6,
               title=text, prop={'size': 8}, title_fontsize=8)
    plt.title(title)

    # set x axis major ticks to month starts
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
