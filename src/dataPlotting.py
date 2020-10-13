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

import matplotlib
import matplotlib.dates as mp_dates
import numpy as np
import pandas

# if environment variable MPL_NO_AGG is set to '1', we do not want to switch to no-GUI backend 'Agg' for plotting
if not os.getenv('MPL_NO_AGG') == "1":
    matplotlib.use('Agg')  # to be able to plot without GUI (e.g. on a headless server), this must be set before importing pyplot

from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator as mpl_MultipleLocator, MaxNLocator as mpl_MaxNLocator
from matplotlib.collections import LineCollection
from matplotlib.offsetbox import AnchoredOffsetbox, TextArea, VPacker

import dataFiles
import dataMangling

weeklyIncidenceLimit1Per100k = 35
weeklyIncidenceLimit2Per100k = 50


def plot_timeseries(datacolumns, dates, daily, cumulative, title, filename, population, max_prevalence_100k=None, ifShow=True, ifCleanup=True, isKreis=True):
    """Creates the image with the different statistic graph plots for the covid-19 cases of a country, Bundesland or Kreis"""

    # enlarger for y-limits of axis' tick ranges to not plot too close to top
    PLOT_YLIM_ENLARGER_DAILYS = 1.3  # if this is too low (e.g. 1.2), chances are good that some daily graphs go beyond the top, due to below manual changes to automatic ticks
    PLOT_YLIM_ENLARGER_CUMU = 1.1
    # plotting color for 7-daily sums graph
    COLOR_INCID_SUMS = '#2020D0'

    lns0, lns1, lns1_0, lns3, lns3_0, lns3_1, lns4_1, lns4_2, lns5, lns6_1, lns6_2 = [], [], [], [], [], [], [], [], [], [], []

    ax: plt.Axes # type hint for better IDE auto-completion
    fig, ax = plt.subplots(figsize=(10, 6))  # , constrained_layout=True)

    # add axis for cumulative total cases (with seperate y-axis), and background gradient
    ax_cumu: plt.Axes = ax.twinx()

    # ax for background gradient
    ax_bg: plt.Axes = ax.twinx()
    ax_bg.set_ylim(0, cumulative[-1] * PLOT_YLIM_ENLARGER_DAILYS)
    ax_bg.grid(False)
    ax_bg.tick_params(axis='y', width=0)
    ax_bg.set_yticklabels([])

    # take care for not plotting background gradient over the rest, and not plot ax white background over the rest
    ax_bg.set_zorder(1)
    ax.set_zorder(2)
    ax.set_frame_on(False) # let lower zorder ax shine through
    ax_cumu.set_zorder(3)

    # default ax to plot expactation day marker on (should be over all others)
    ax_for_marker = ax

    # if isKreis, add axis for daily sums (with seperate y-axis), set z-order, use for marker
    if isKreis:
        ax_sum: plt.Axes = ax.twinx()
        ax_sum.set_zorder(4)
        ax_for_marker = ax_sum
    else:
        ax_sum = ax # just a dummy to stop IDEs from crying about maybe uninitialized variable


    # set grids
    ax.grid(True, which='major', axis='x', ls='-', alpha=0.9)  # if not set here above, major ticks of x axis won't be visible
    ax.grid(True, which='minor', axis='x', ls='--', alpha=0.5)  # if not set here above, minor ticks of x axis won't be visible
    # ax.grid(True, which='major', axis='y', ls='-', alpha=0.7)  # if not set here above, ticks of left side y axis won't be visible
    # ax.grid(True, which='minor', axis='y', ls='--', alpha=0.5)

    # set x axis minor tick interval to only each 5 days one tick, as compromise between being exact and easily readable
    fig.autofmt_xdate(rotation=60)
    ax.xaxis_date()
    ax.xaxis.set_minor_locator(matplotlib.dates.DayLocator(bymonthday=range(1, 30, 5)))

    #
    # plot background gradient, indicating relative prevalence
    if max_prevalence_100k is not None and not "Deutschland" in filename:
        # backgroud gradient indicating local max prevalence values compared with global
        glob_max = max_prevalence_100k
        mid = mp_dates.date2num(dates)[int(len(dates) / 2)]  # get middle point of the dates as plot start point
        # create some artificially plotting points, at the x-middle point of the dates, from zero up the y-axis' maximum
        points = np.array([[mid] * len(dates), np.linspace(0, cumulative[-1] * PLOT_YLIM_ENLARGER_DAILYS, len(dates))]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1) # create lines from neighbour to neighbour of elements in 'points'
        # set proportion for colors, matching plot item's own 100k prevalence
        proportion = np.linspace(0, max(cumulative / population * 100000) * PLOT_YLIM_ENLARGER_DAILYS, len(dates))
        # set norm to match global max, shooting the colors over the plot item's max, if it is not the global prevalence max itself
        #   this norm together with the max of 'proportion' is basically the core, to indicate the relative prevalence
        norm = plt.Normalize(0, glob_max)
        cmap = 'YlOrRd' if isKreis else 'Reds'
        lc = LineCollection(segments, cmap=cmap, norm=norm, alpha=0.4)
        lc.set_array(proportion)
        lc.set_linewidth(6 * fig.dpi) # plot with enough width to fill the background horizontally

        # TODO: place color bar for prevalence background gradient in cumu axe?
        # axcb = plt.colorbar(lc)
        # axcb.set_label('prevalence indicator')
        ax_bg.add_collection(lc)

    #
    # plot raw daily cases
    if not isKreis:
        ax.plot(dates, daily, color='w', linewidth=7, alpha=0.1) # plot white background for next line
    red_days = 5 # '5' matches the minor ticks on x-axis
    lns1 = ax.plot(dates, daily, label=f"raw daily cases (weekend-flawed), red: last {red_days}", color='#B0B0B0', zorder=1)
    ax.plot(dates[-red_days:], daily[-red_days:], color='#FF8080')
    # lns1 = ax.plot(dates, daily, label="daily cases (weekend-flawed), 2 weeks: red", color='#AAAAAA')
    # lns1_2 = ax.plot(dates[-14:], daily[-14:], label="daily cases, last 14 days dark gray", color='red')
    # print (len(dates[-14:]))

    # set y1 axis tick automatic interval and range restrictions, allow no 'half daily cases' (no floating point numbers)
    yloc = mpl_MaxNLocator(integer=True)
    ax.yaxis.set_major_locator(yloc)
    ax.set_ylim(0, max(daily[1:]) * PLOT_YLIM_ENLARGER_DAILYS)


    #
    # plot cumulative cases data for the 2nd y axis
    ax_cumu.plot(dates, cumulative, color='w', linewidth=7, alpha=0.1) # plot white background for next line
    lns5 = ax_cumu.plot(dates, cumulative, label="total cases reported at RiskLayer", color='#50C0FF', linestyle='dotted', linewidth=2)

    ax_cumu.set_ylim(0, max(cumulative) * PLOT_YLIM_ENLARGER_CUMU)
    ax_cumu.set_ylabel("cumulative total cases")
    ax_cumu.yaxis.label.set_color(color=lns5[0].get_color())
    ax_cumu.tick_params(axis='y', colors=lns5[0].get_color())

    #
    # plot rolling average
    # rolling averages for daily cases, over two weeks
    window = 14
    rolling_mean = pandas.DataFrame(daily).rolling(window=window, center=True).mean()
    rmean_data = rolling_mean[0]
    if not isKreis:
        ax.plot(dates, rolling_mean, color='w', linewidth=11, alpha=0.1)  # plot white background for next line
        lns3 = ax.plot(dates, rolling_mean, label="centered moving average, %s days cases" % window, color='#FFD010', linewidth=3, zorder=2)
    else:
        lns3 = ax.plot(dates, rolling_mean, label="centered moving average, %s days cases" % window, color='#FFD010', linewidth=3, zorder=0)
        ax.fill_between(dates, rmean_data, [0] * len(dates), label="centered moving average, %s days cases" % window,
                                 color=lns3[0].get_color(), linewidth=0, zorder=0)

    #
    # multi colored y-axis label
    ybox1 = TextArea("raw daily cases", textprops=dict(color=lns1[0].get_color(), rotation='vertical'))
    ybox2 = TextArea(" / ", textprops=dict(color="black", rotation='vertical'))
    ybox3 = TextArea("moving average", textprops=dict(color=lns3[0].get_color(), rotation='vertical'))
    ybox = VPacker(children=[ybox3, ybox2, ybox1], align="center", pad=0, sep=5)
    anchored_ybox = AnchoredOffsetbox(loc=8, child=ybox, pad=0., frameon=False,
                                      bbox_to_anchor=(-0.08, 0.2),  # if first value smaller than -0.08 we get in trouble with graph for country
                                      bbox_transform=ax.transAxes, borderpad=0.)
    ax.add_artist(anchored_ybox)

    #
    # plot rolling sum of prior 7 days cases for date, if it is a Kreis, where the according incidence borders are of interest
    yminor = 0
    if isKreis:
        # plot 7 day sums, only if incidence borders can be calculated via population
        # according grid for it
        ax_sum.grid(True, which='major', axis='y', ls='-', alpha=0.6, color=COLOR_INCID_SUMS)  # if not set here above, ticks of left side y axis won't be visible
        ax_sum.grid(True, which='minor', axis='y', ls='--', alpha=0.2, color=COLOR_INCID_SUMS)

        yloc2 = mpl_MaxNLocator(integer=True)
        ax_sum.yaxis.set_major_locator(yloc2)

        # move total cases y axis away to outside
        ax_cumu.spines["right"].set_position(("axes", 1.15))

        # sum calculation and plotting
        window = 7
        label = 'sum of daily cases, for prior %s days of date' % window
        rolling_sum = pandas.DataFrame(daily).rolling(window=window, center=False).sum()
        rolling_sum_max = rolling_sum[0].max()

        # plot yellow background for sum graph, then graph over it
        ax_sum.plot(dates, rolling_sum, label=label, color='yellow', linewidth=7, alpha=0.4)
        lns0 = ax_sum.plot(dates, rolling_sum, label=label, color=COLOR_INCID_SUMS)

        # set axis properties
        ax_sum.set_ylim(0, rolling_sum_max * PLOT_YLIM_ENLARGER_DAILYS)
        # also yellow background for label
        ax_sum.set_ylabel(label + "\n(to determine incidence borders)", color=COLOR_INCID_SUMS,
                          bbox=dict(color='yellow', alpha=0.3, boxstyle='round', mutation_aspect=0.5))
        ax_sum.tick_params(axis='y', colors=COLOR_INCID_SUMS, size=4, width=1.5)

        # adjust sum y axis visibilities
        ax_sum.set_frame_on(True)
        ax_sum.patch.set_visible(False)
        for sp in ax_sum.spines.values():
            sp.set_visible(False)
        ax_sum.spines["right"].set_visible(True)

        # calculate some good value for minor ticks
        yticks = yloc2()
        ydiff = yticks[1]
        yminor = int(ydiff / 5 + 0.5) if ydiff >= 8 else 1
        ax_sum.yaxis.set_minor_locator(mpl_MultipleLocator(yminor))

        # plot incidence border lines
        limit = weeklyIncidenceLimit1Per100k * population / 100000
        lns6_1 = ax_sum.plot([dates[0]] + [dates[-1]], [limit, limit],
                             label="incid. border %i/week/100k pop.: %.2f" % (weeklyIncidenceLimit1Per100k, limit), color='#ff8c8c',
                             linestyle=(0, (3, 5)))

        # plot second incidence border only if first one is nearly reached, to have no unneeded large y1 numbers which would worsen the view
        if rolling_sum_max > limit * 0.8:
            limit = weeklyIncidenceLimit2Per100k * population / 100000
            lns6_2 = ax_sum.plot([dates[0]] + [dates[-1]], [limit, limit],
                                 label="incid. border %i/week/100k pop.: %.2f" % (weeklyIncidenceLimit2Per100k, limit), color='#df4c4c',
                                 linestyle=(0, (5, 4)))
        ax_sum.set_ylim(0, max(rolling_sum_max, limit) * PLOT_YLIM_ENLARGER_DAILYS)

        # set new ax limit for daily cases / averaging, trying to have evenly distributed major ticks for both y axes
        #   this will work in many cases, but still some work would be todo to get all left/right major ticks in same grid
        ax.set_ylim(0, yloc()[-2])
        ax_sum.set_ylim(0, yloc2()[-2])
        yticks = yloc2()
        ydiff = yticks[1]
        yminor = int(ydiff / 5 + 0.5) if ydiff >= 8 else 1  # '+0.5' to round up for '8'
        ax_sum.yaxis.set_minor_locator(mpl_MultipleLocator(yminor))
        # the '0.25'-multiplier below, for setting the y-position of the marker, is a none-deterministic evaluated value which lets the
        #   triangle marker's bottom point be placed nearly at the x-axis, for all of the 400+ Kreise with their different case numbers
        yminor *= 1.3

    if not isKreis:
        #
        #  plot rolling averages for daily cases, over a wekk, if not a Kreis
        window = 7
        rolling_mean = pandas.DataFrame(daily).rolling(window=window, center=True).mean()
        rmean_data = rolling_mean[0]
        ax.plot(dates, rolling_mean, color='w', linewidth=7, alpha=0.1)  # plot white background for next line
        lns6_1 = ax.plot(dates, rolling_mean, label="centered moving average, %s days cases" % window, color='#900090', zorder=3)

        ax.grid(True, which='major', axis='y', ls='-', alpha=0.9)  # if not set here above, ticks of left side y axis won't be visible
        ax.grid(True, which='minor', axis='y', ls='--', alpha=0.7)

        # determine some meaningfull y1 minor tick value, also used for setting center bar's y position
        yticks = yloc()
        ydiff = yticks[1]
        yminor = int(ydiff / 5 + 0.5) if ydiff >= 8 else 1  # '+0.5' to round up for '8'
        ax.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(yminor))
        # the '1.3'-multiplier below, for setting the y-position of the marker, is a none-deterministic evaluated value which lets the
        #   triangle marker's bottom point be placed nearly at the x-axis, for all of the 16 Bundeslaender with their different case numbers
        yminor *= 1.3

    #
    # plot marker for temporal center date
    center, signal = dataMangling.temporal_center(daily)
    center_date = datacolumns.values[int(round(center))]
    # (first a dummy marker just for later showing in legend with smaller symbol, gets plotted over with 2nd one)
    lns4_1 = ax_for_marker.plot(dates[int(round(center))], [yminor], marker="v", color='green', markersize=8, label="marker for 'expectation day': " + center_date,
                                linestyle="")
    # (side note: if markersize here would be an odd number, the triangle would be skewed)
    ax_for_marker.plot(dates[int(round(center))], [yminor], marker="v", color='green', markersize=16, zorder=4)

    #
    # build legend
    # collect lines which shall get a label in legend
    lines = lns4_1 + lns5 + lns1 + lns3 + lns0 + lns6_2 + lns6_1
    labs = [l.get_label() for l in lines]

    # text for legend
    text = "source data: ©RiskLayer up to " + ("%s" % max(dates))[:10]
    text += " – plot:\n©DrAndreasKruger (+contrib.) " + ("%s" % datetime.datetime.now())[:16]
    # text += "\ndaily: (GREEN) 'expectation day' = " + center_date

    # plot legend on top axis, and title
    ax_for_marker.legend(lines, labs, loc='upper left', facecolor="#fafafa", framealpha=0.7, title=text, prop={'size': 8}, title_fontsize=8)
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

    return plt, fig, ax, ax_cumu


def test_plot_Kreis(ts, bnn, dates, datacolumns):
    ## Kreis
    AGS = "0"
    # AGS = "1001"
    AGS = "5711"
    # AGS = "3455"

    ts, bnn, ts_sorted, Bundeslaender_sorted, dates, datacolumns = dataMangling.dataMangled(withSynthetic=False)
    max_prevalence_100k = dataMangling.get_Kreise_max_prevalence_100k(bnn)

    plot_Kreise(ts, bnn, dates, datacolumns, [AGS], max_prevalence_100k, ifPrint=False, ifShow=True)


def plot_Kreise(ts, bnn, dates, datacolumns, Kreise_AGS, max_prevalence_100k, ifPrint=True, ifShow=False):
    done = []
    for AGS in Kreise_AGS:
        daily, cumulative, title, filename, pop = dataMangling.get_Kreis(ts, bnn, AGS)
        plot_timeseries(datacolumns, dates, daily, cumulative, title, population=pop, max_prevalence_100k=max_prevalence_100k,
                        filename=filename, ifShow=ifShow)
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


def plot_Kreise_parallel(ts, bnn, dates, datacolumns, Kreise_AGS, max_prevalence_100k, ifPrint=True):
    import multiprocessing as mp

    # one CPU should be left free for the system, and multiprocessing makes only sense for at least 2 free CPUs,
    # so just call the non-parallel version if not enough CPUs are in the system
    available_cpus = mp.cpu_count()
    leave_alone_cpus = 1
    wanted_cpus = available_cpus - leave_alone_cpus

    if available_cpus < wanted_cpus or wanted_cpus < 2:
        return plot_Kreise(ts, bnn, dates, datacolumns, Kreise_AGS, max_prevalence_100k, ifPrint=ifPrint)

    done = []

    # setup process pool
    pool = mp.Pool(wanted_cpus)
    try:
        done = pool.starmap(plot_Kreise, [(ts, bnn, dates, datacolumns, [AGS], max_prevalence_100k, ifPrint) for AGS in Kreise_AGS])
    except KeyboardInterrupt:
        # without catching this here we will never be able to manually stop running in a sane way
        pool.terminate()
    finally:
        pool.close()
        pool.join()

    return done


def test_plot_Bundesland(ts, bnn, dates, datacolumns, Bundesland="Bayern", ifShow=True):
    ## Bundesland
    # Bundesland = "Dummyland"

    ts_BuLa, Bundeslaender = dataMangling.join_tables_for_and_aggregate_Bundeslaender(ts, bnn)
    BL = Bundeslaender.drop(labels=['Deutschland', 'Dummyland'])
    max_prevalence_100k = max(BL[BL.columns[-2]] / BL[BL.columns[-1]]) * 100000

    daily, cumulative, title, filename, population = dataMangling.get_BuLa(Bundeslaender, Bundesland, datacolumns)
    plot_timeseries(datacolumns, dates, daily, cumulative, title, filename, population, max_prevalence_100k, ifShow=ifShow, isKreis=False)


def plot_all_Bundeslaender(ts, bnn, dates, datacolumns, ifPrint=True):
    ts_BuLa, Bundeslaender = dataMangling.join_tables_for_and_aggregate_Bundeslaender(ts, bnn)
    filenames, population = [], 0
    done = []

    BL = Bundeslaender.drop(labels=['Deutschland', 'Dummyland'])
    max_prevalence_100k = max(BL[BL.columns[-2]] / BL[BL.columns[-1]]) * 100000
    # print(max_prevalence_100k)

    for BL in Bundeslaender.index.tolist():
        print(BL, end=" ")
        daily, cumulative, title, filename, pop_BL = dataMangling.get_BuLa(Bundeslaender, BL, datacolumns)
        if BL == "Deutschland":
            filename = filename.replace("bundesland_", "")
        plot_timeseries(datacolumns, dates, daily, cumulative, title, population=pop_BL,
                        filename=filename, max_prevalence_100k=max_prevalence_100k,
                        ifShow=False, isKreis=False)
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
        max_prevalence_100k = dataMangling.get_Kreise_max_prevalence_100k(bnn)
        plot_Kreise(ts, bnn, dates, datacolumns, ts["AGS"].tolist(), max_prevalence_100k)
        plot_all_Bundeslaender(ts, bnn, dates, datacolumns)
