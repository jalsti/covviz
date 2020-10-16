#!/usr/bin/env python3
"""

@summary: download, store, load, inspect, ... several different sources

@version: v03.5 (26/June/2020)
@since:   25/April/2020

@author:  Dr Andreas Krueger
@see:     https://github.com/covh/covviz for updates

@status:  Cleaned up. Has function comments! For now, needs not much attention.
          PERHAPS: refactor CONSTANTS into SETTINGS.py ? Reorder calls in main()?
@todo:    Feedback please: This is how I would comment and clean the other .py files.
                           Good? Suggestions?

"""

import os, shutil, hashlib, time, datetime, sys
import pandas, wget, requests, numpy
import bs4 as bs
import pandas as pd

REPO_PATH = ".."
DATA_PATH = os.path.join(REPO_PATH, "data")
BNN_FILE = os.path.join(DATA_PATH, "GermanyKreisebene_Risklayer_bnn-20200425.csv")
HAUPT_FILES = os.path.join(DATA_PATH, "GermanyKreisebene_Risklayer_haupt%s.csv")
WP_FILE =  os.path.join(DATA_PATH, "wikipedia_kreise_most.csv")
WP_URL="https://de.wikipedia.org/"

TS_FILE =  os.path.join(DATA_PATH, "GermanyValues_RiskLayer-20200425.csv")
TS_NEWEST =  os.path.join(DATA_PATH, "GermanyValues_RiskLayer.csv")
PICS_PATH = os.path.join(DATA_PATH, "..", "pics")
PAGES_PATH = os.path.join(DATA_PATH, "..", "pages")

WWW_REPO_PATH = os.path.join(DATA_PATH, "..", "..", "cov19de")
WWW_REPO_PICS = os.path.join(WWW_REPO_PATH, "pics")
WWW_REPO_PAGES = os.path.join(WWW_REPO_PATH, "pages")
WWW_REPO_PATH_GIT_SCRIPT = "./git-add-commit-push.sh"

ALSO_TO_BE_COPIED = ["index.html", "history.txt", "todo.md", "log.txt"]

RISKLAYER_URL01 = "http://risklayer-explorer.com/media/data/events/GermanyValues.csv"
# RISKLAYER_URL02 = "https://docs.google.com/spreadsheets/d/1wg-s4_Lz2Stil6spQEYFdZaBEp8nWW26gVyfHqvcl8s/"
# RISKLAYER_URL02_SHEET = "bnn"

# naming 'Haupt' (in case they reorder their sheets, then gid=0 would point to the wrong one!)
# for syntax see https://stackoverflow.com/a/33727897
#     and https://developers.google.com/chart/interactive/docs/spreadsheets#query-source-ranges
#
# https://docs.google.com/spreadsheets/d/1EZNqMVK6hCccMw4pq-4T30ADJoayulgx9f98Vui7Jmc/gviz/tq?tqx=out:csv&range=A5:AU406&sheet=Haupt
GOOGLEDOCS_ToCSV_WithSheetname="https://docs.google.com/spreadsheets/d/%s/gviz/tq?tqx=out:csv&sheet=%s&range=%s"
# RISKLAYER_MASTER_SHEET_20200521 = "1EZNqMVK6hCccMw4pq-4T30ADJoayulgx9f98Vui7Jmc" # last night snapshot
RISKLAYER_MASTER_SHEET = "1wg-s4_Lz2Stil6spQEYFdZaBEp8nWW26gVyfHqvcl8s" # Risklayer master: https://docs.google.com/spreadsheets/d/1wg-s4_Lz2Stil6spQEYFdZaBEp8nWW26gVyfHqvcl8s
RISKLAYER_MASTER_SHEET_TABLE = ("Haupt", "A5:AU406")
# the columns containing the web-URL-sources changed over time:
QUELLEN_SPALTEN={"v01": ['Quelle 1', 'Gestrige Quellen', 'Quelle (Sollte nur Landesamt, Gesundheitsamt oder offiziell sein)', 'TWITTER', 'FACEBOOK/INSTAGRAM', 'Names'],
                 "v02": ['Quelle 1',                     'Quelle (Sollte nur Landesamt, Gesundheitsamt oder offiziell sein)', 'TWITTER', 'FACEBOOK/INSTAGRAM', 'Names'] }

VERSION_HISTORY_TABLE = {"sheetID"   : "1rn_nPJodxAwahIzqfRtEr9HHoqjvmh_7bj6-LUXDRSY",
                         "sheetName" : "ThePast",
                         "range" :     "A3:E12"}

# distances between districts:
OPENDATASOFT_URL01 = "https://public.opendatasoft.com/explore/dataset/covid-19-germany-landkreise/table/"
OPENDATASOFT_URL02 = "https://public.opendatasoft.com/explore/dataset/covid-19-germany-landkreise/download/?format=csv&lang=en&use_labels_for_header=true&csv_separator=%3B"
OPENDATASOFT_PATH = os.path.join(DATA_PATH, "covid-19-germany-landkreise.csv")
DISTANCES_PATH = os.path.join(DATA_PATH, "distances.csv")


########################### download, store, and repair timeseries data ########################################

def swap_specific_typo_cells(df, correct_type, wrong='o', correct='0'):
    """
    Sometimes, riskLayer makes a new typo in the CSV file.

    This is hopefully useful, as an abstraction to fix that faster in future cases.
    It will always need some manual interaction but this should speed it up.

    1 search for any occurence of 'o'
    2 go through all rows (indices) affected
    3 find the specific columns with 'o'
    4 correct the data, by overwriting with '0'
    5 cast all those affected columns to <class 'numpy.float64'>
    6 return a corrected dataframe, and the rows - if the latter is empty, nothing had happened.
    """

    print("Searching for '%s' instead of '%s':" %(wrong, correct))
    typos = df[df.astype(str).eq(wrong).any(1)]
    affected_cols=[]
    for i in typos.index:
        print ("row index", i)
        cols=df.columns[df.loc[i].astype(str)==wrong].tolist()
        # print(cols)
        for col in cols:
            print(col, ":", df.loc[i,col], end=" --> ")
            df.loc[i,col]=correct
            print(df.loc[i,col])
        affected_cols.extend(cols)

    if affected_cols:
        print ("Done. Now casting affected columns %s to %s" % (affected_cols, correct_type))
        for col in affected_cols:
            df[col]=df[col].astype(correct_type)

    return df, affected_cols


def testing_swap_specific_typo_cells():
    """
    test the above.
    """
    df=pandas.read_csv(TS_NEWEST, encoding='cp1252')

    print("\ndefault example with 'o' instead of '0':")
    swap_specific_typo_cells(df, correct_type=type(df.loc[1, "01.06.2020"]))

    print("\nexample with 'docs' instead of '0':")
    df, cols=swap_specific_typo_cells(df, correct_type=type(df.loc[1, "01.06.2020"]), wrong='docs', correct=0)
    if not cols:
        print("Looks like they've repaired it.")

    print("\nexample with several findings:")
    swap_specific_typo_cells(df, correct_type=type(df.loc[1, "01.06.2020"]), wrong='601.0', correct=601.0)


def show_problematic_columns(df, type_wanted=numpy.float64, how_many_different=2):
    """
    if there is a typo in any cell, pandas might change the numerical/string type for the whole column
    """
    cols = df.columns[df.dtypes!=type_wanted].tolist()
    if len(cols)>how_many_different:
        print("There are columns which are not '%s': %s" % (type_wanted, cols))


def remove_unnecessary_columns(ts, wrong=["Population"]):

    unwanted = list( set(wrong) - ( set(wrong) - set(list(ts.columns))) )

    if unwanted:
        print("\nUnwanted column-names detected (new problem since Sept 11th): ", unwanted, end=" ... ")
        ts.drop(unwanted, axis=1, inplace=True)
        print ("DROPPING that column" + ("s" if len(unwanted) > 1 else "" ) + ".\n")
    else:
        print ("No unwanted columns (%s) detected (problem appeared Sept 11th), continuing with unchanged table ...\n" % wrong)

    return ts

def repairData(ts):
    """
    The CSV contains some data typos.

    This will get better when they automate the procedure to create the CSV, see their "Fragen und Antworten" sheet.
    These problems are patched here:

    12.03.20203
    ï»¿AGS
    1733.0  -->   1.739  -->  1743.0
    'docs'
    'o'
    """

    print ("\nRepair dirty risklayer data:")

    show_problematic_columns(ts)

    ts=remove_unnecessary_columns(ts)

    newcols = ["12.03.2020" if x=="12.03.20203" else x for x in ts.columns]
    if newcols!=ts.columns.tolist():
        print ("found and fixed 12.03.20203 --> 12.03.2020 (problem since 25/4/2020)")

    newcols2 = ["AGS" if x=='ï»¿AGS' else x for x in newcols]
    if newcols2!=newcols:
        print ("found and fixed ï»¿AGS --> AGS  (problem since 29/4/2020)")

    ts.columns = newcols2


    before = ts[ts["AGS"]=="05370"]["27.04.2020"]
    after  = ts[ts["AGS"]=="05370"]["28.04.2020"]
    # print (float(after) / float(before) )
    if float(after) / float(before) < 0.5:
        print ("huge drop of some values for 28.4.2020, e.g. Heinsberg: 1733.0  -->   1.739  -->  1743.0 (was a problem on 29/4/2020)")
        print ("temporary fix: interpolate 28. from 27. and 29.")
        ts["28.04.2020"]=(ts["29.04.2020"]+ts["27.04.2020"])/2


    # print (ts.index.tolist()); exit()
    colproblem, colgood= "10.03.2020", "09.03.2020"

    typo='docs' # problem appeared in 25.05.2020 file:
    ii=ts[ts[colproblem].astype(str)==typo].index.values.tolist()
    # print(ii)
    if ii:
        print ("found typo '%s' in datafile at positions [%s, %s] (was a problem on 25/5/2020)" % (typo, ii, colproblem), end=" ")
        if len(ii)>1:
            raise Exception("ALARM: SEVERAL")
        i=ii[0]
        # print(ts.loc[i,"10.03.2020"])
        ts.loc[i,colproblem]=ts.loc[i,colgood]
        # print(ts.loc[i,"10.03.2020"])

        # ts=ts.drop([401, 402, 403])
        print ("overwritten with previous day value. Now cast whole column to 'float':", end=" ")
        ts[colproblem]=ts[colproblem].astype(float)
        print ("Done.")


    # wrong, correct='o',0 # typo 'o' instead of 0
    # df, cols = swap_specific_typo_cells(ts, correct_type=type(ts.loc[1, "01.06.2020"]), wrong=wrong, correct=correct)
    # if cols:
    #     print("found and fixed typo '%s' which had cast whole column/s %s to string. Corrected that now. (appeared on June 2nd 2020)" % (wrong, cols))
    #     ts=df
    # else:
    #     print("They fixed that problem (which had appeared on June 2nd).")

    # perhaps there are still columns that need fixing:
    show_problematic_columns(ts)

    print()
    return ts


def pandas_settings_full_table():
    """
    simple hack to let pandas print a larger column
    """
    pandas.set_option('display.max_columns', None)
    pandas.set_option('display.width', 200)
    pandas.set_option('display.max_rows', None)


def inspectNewestData(ts, alreadyRepaired=False):
    """
    Sometimes values are corrected down, that's fine.
    However, if that happens too often, it's a sign that there's possibly data corruption somewhere.
    Use this for visual inspection.

    # TODO:
    # when this became 91 rows, with sometimes > 1500 cases dropped
    # it helped to find out that the source data was errorenous.
    # perhaps in the future, let the overall script fail?
    # Send an email to admin?
    # For now it simply prints an ALERT, but only by number of rows,
    # and not yet by total negative diff.
    """

    if not alreadyRepaired:
        ts = repairData(ts)

    # print (ts.columns)
    lastColumns=["ADMIN"] + ts.columns[-5:].tolist()
    df = ts[lastColumns]
    print ("\nJust visual inspection - unless the following tables get VERY LONG - all is probably good ...\n(TODO: Automate this with two thresholds (number of, amount of drop)?)\n")

    pandas_settings_full_table()

    down_prev=df[df[lastColumns[-2]]<df[lastColumns[-3]]]
    if len(down_prev)>20:
        print (("*"*100 + "\n")*3)
        print ("ALERT: Alarmingly many - ", end=" ")
    print ("%d values going DOWN for previous day:" % len(down_prev))
    time.sleep(2)
    if len(down_prev):
        print (down_prev)
    print()

    down_last=df[df[lastColumns[-1]]<df[lastColumns[-2]]]
    if len(down_last)>20:
        print ("ALERT: Alarmingly many - ", end=" ")
    print ("%d values going DOWN for newest day:" % len(down_last))
    time.sleep(2)
    if len(down_last):
        print (down_last)
    print()

    print()
    print ("Totals:")
    datecolumns=ts.columns[-9:].tolist()
    df = ts[datecolumns].sum()
    # df["diff"]=df.diff()
    print (df.astype(int).to_string())
    print ("Diffs:")
    print (df.diff().dropna().astype(int, errors='ignore').to_string())
    # print (df)


def hash_file(filename):
    """
    hash the file content, to be able to tell whether two files are identical.
    """
    with open(filename,"rb") as f:
        allbytes = f.read() # read entire file as bytes
        readable_hash = hashlib.sha256(allbytes).hexdigest();
    # print(readable_hash)
    return readable_hash


def true_if_exist_and_equal(filenames):
    """
    checks that files exist, AND that they are equal in content.
    """
    if len(filenames)<2:
        raise Exception("must compare more than one file.")
    hashes=[]
    for filename in filenames:
        try:
            hashes.append(hash_file(filename))
        except Exception as e:
            print(type(e), e) # TOO: perhaps comment away?
            print ("didn't exist, means new data available, downloaded, and stored:")
            return False
    unique=list(set(hashes))
    return len(unique)==1


def test_comparison():
    """
    test the above
    """
    for filenames in [["test1.txt", "test2.txt"], ["test1.txt", "test3.txt"]]:
        print (filenames, true_if_exist_and_equal(filenames))


def read_as_CSV_or_as_SSV(filename, encoding='utf-8'):
    """
    try CSV first - if that fails try reading in as SSV
    Happened first on August 3rd or 4th - suddenly not comma separated anymore but semicolon separated.
    """
    ts = pandas.read_csv(filename, encoding=encoding)
    rows, cols = len(ts), len(ts.columns)
    print ("(rows, cols) = (%s, %s)" % (rows, cols), end=" ")

    # TODO: this should not be necessary, as long as above no sep is given:
    #  → https://pandas.pydata.org/pandas-docs/version/1.0.3/reference/api/pandas.read_csv.html?highlight=read_csv#pandas.read_csv
    if cols == 1:
        print ("\n\nALERT: ERROR in source file: 1 column. Not comma-separated" \
               " but semicolon-separated?? (Happened first on Aug 4th). Trying that now:")
        ts=pandas.read_csv(filename, sep=";", encoding='utf-8')
        rows, cols = len(ts), len(ts.columns)
        print ("(rows, cols) = (%s, %s)" % (rows, cols), end=" ")
    else:
        print ("==> CSV format correct probably (issue on Aug 4th)", end =" ")


    print ("==> looking good. Let's see if it reads in correctly ...\n")
    return ts


def downloadData(andStore=True,
                 url=RISKLAYER_URL01, target=DATA_PATH,
                 ts_file=TS_FILE, ts_newest=TS_NEWEST,
                 encoding='utf-8'): # encoding='cp1252'):
    """
    download, and store in 2 files:
     one timestamped, for possible later use
     one "always the newest", for generating plots & pages

    visual inspection of the data
    returns (bool "that was newly stored data", timeseries)
    """
    print (url)
    filename = wget.download(url, out=target)
    print ("downloaded:", filename)
    ts = read_as_CSV_or_as_SSV(filename, encoding=encoding)

    last_col = ts.columns[2:].tolist()[-1]
    print ("newest column:", last_col)

    d=last_col.split(".")
    d.reverse()
    last_date = "".join(d)
    newfilename = ts_file.replace("20200425", last_date)
    equal = true_if_exist_and_equal([filename, newfilename])

    if andStore:
        print ("Saving into 2 files:")
        shutil.move(filename, newfilename)
        print (newfilename)
        shutil.copy(newfilename, ts_newest)
        print (ts_newest)
    else:
        warn = ("*" * 57 + "\n")*3
        print("\n" + warn + "ALERT: dev mode ... NOT storing this data\n"+ warn)

    inspectNewestData(ts)
    # print ("TODO perhaps")
    # print (RISKLAYER_URL02)
    # print ("sheet", RISKLAYER_URL02_SHEET)

    # Say if a new file was created. Also return the dataFrame itself.
    return not equal, ts


def downloadDataNotStoring(url=RISKLAYER_URL01, encoding='utf-8'):
    """
    good for readonly files system like on heroku
    """
    print (url)

    # ts=pandas.read_csv(url, encoding='utf-8') # 'cp1252') # encoding='utf-8')
    ts = read_as_CSV_or_as_SSV(filename=url, encoding=encoding)

    return ts


########################### load & prepare timeseries #######################################################

def attribution_and_repair(ts):
    """
    print the 3 infolines, then drop them. repair the typos.
    """
    print ("\nLoading data from RiskLayer. This is their message:")
    print ("\n".join(ts[ts.ADMIN.isna()][ts.columns[0]].tolist()))
    print()
    # now drop those info lines which are not data:
    ts.drop(ts[ts.ADMIN.isna()].index, inplace=True)
    ts = repairData(ts)
    return ts


def load_data(ts_f=TS_NEWEST, bnn_f=BNN_FILE, ifPrint=True, encoding='utf-8'):
    """
    load timeseries and population sizes; incl attribution_and_repair(ts);
    """
    bnn=pandas.read_csv(bnn_f)

    # ts=pandas.read_csv(ts_f, encoding='cp1252') # encoding='utf-8')
    ts = read_as_CSV_or_as_SSV(filename=ts_f, encoding=encoding)

    ts = attribution_and_repair(ts)
    return ts, bnn


def add_synthetic_data(ts, bnn, flatUntil = 14, steps=[10, 20, 50, 100, 130, 140, 150]):
    """
    synthetic district helps to understand better the plots, averaging functions, etc.
    # infection steps: plus 10 plus 10 plus 30 plus 50, plus 30 plus 10 plus 10
    """
    synthetic_data = [0]*flatUntil  + steps + ([steps[-1]] * (len(ts.columns)-2-flatUntil-len(steps)))
    row = pandas.Series(["00000", "Dummykreis"]+synthetic_data, index=ts.columns)
    ts=ts.append(row, ignore_index=True)

    # some deterministic demography data, e.g. for unit testing
    synthetic_landkreis = [0, "Dummykreis", "Landkreis", 150000, 100, 0.67,
                           0, 300,"Dummyland", 400000, 0.75]
    row = pandas.Series(synthetic_landkreis, index=bnn.columns)
    bnn=bnn.append(row, ignore_index=True)

    return ts, bnn

def data(withSynthetic=True, ifPrint=True):
    """
    load data, show attribution, repair data, possibly add synthetic district
    returns (time series, population-in-district table)
    N.B.: The bnn table contains more info but not uptodate, so just ignore it. TODO: drop all those columns.
    """
    ts, bnn = load_data(ifPrint=ifPrint)
    if withSynthetic:
        ts, bnn = add_synthetic_data(ts, bnn)
    return ts, bnn


################################### master googlesheet ... 'Haupt' #############################################

def download_sheet_table(sheetID=RISKLAYER_MASTER_SHEET, table=RISKLAYER_MASTER_SHEET_TABLE, reindex="AGS"):
    """
    download from risklayer mastersheet ... just one sheet 'Haupt', and only selected rows&columns, see 'table' info
    make AGS columns into row index for the DataFrame, for easier access
    """
    risklayer_sheet_url = GOOGLEDOCS_ToCSV_WithSheetname % (sheetID, table[0], table[1])
    print ("Downloading this data:")
    print (risklayer_sheet_url)
    df=pandas.read_csv(risklayer_sheet_url) # N.B.: If this fails with 'Error tokenizing data ... expected ... saw', then "Share" and switch access to "Anyone on the Internet with this link can view"
    if reindex:
        df.index=df[reindex].tolist() # index == AGS, easier accessprint("to_datetimes\n", to_datetimes)
    #print(df.columns.tolist())
    return df


def find_correct_zeitformat(df, zeitcolumn='Zeit'):
    """
    Sometimes column 'Zeit' has seconds, sometimes not. *Sigh*.

    So, find a first string (i.e. non-nan) entry in 'zeit' column, while iterating rows.
    That decides which format is used for the whole column.
    """
    rows, hit = df.iterrows(), 0.0
    while type(hit) != str:
        row = next(rows)
        hit = row[1][zeitcolumn]
        print(row[0], type(hit), hit, end=" ")

    # sometimes Zeit has seconds, sometimes not, sigh:
    if len(hit)   == len("24/03/2020 09:30:00"):
        zeitformat=        "%d/%m/%Y %H:%M:%S"
    elif len(hit) == len("18/03/2020 20:00"):
        zeitformat=        "%d/%m/%Y %H:%M"
    else:
        msg="Row '%s' was the first of type 'string' in column '%s' but the entry was '%s'. Please add a timeformat implementation for that." %(row[0], zeitcolumn, hit)
        raise Exception(msg)

    print ("--> zeitformat = '%s'" % zeitformat)
    return zeitformat


def generate_filename_from_newest_entry_timestamp(df, filestump=HAUPT_FILES, zeitcolumn="Zeit", maxdate=None):
    """
    column 'Zeit' turned into datetime, drop nan, turn into string for sorting, take max()
    return timestamped filename.

    if downloading historical sheets, better use a maxdate, because
    the newest date in 'Zeit' column enters the filename - and there can be typos or =NOW() entries.
    """
    # pandas_settings_full_table()
    # print ("df.Zeit\n", df.Zeit)

    zeitformat = find_correct_zeitformat(df, zeitcolumn=zeitcolumn)

    # became more complicated on June 1st because pandas read 01/06/2020 wrongly as 6th of January. The dropna is probably not needed? But anyways, we focus on the newest date only so typos don't matter....
    to_datetimes = pandas.to_datetime(df[zeitcolumn], format=zeitformat, errors='coerce')
    # print("to_datetimes\n", to_datetimes)
    #print("to_datetimes dropna\n", to_datetimes.dropna())
    to_datetimes_strings = to_datetimes.dropna().dt.strftime("%Y%m%d_%H%M%S")
    # pandas_settings_full_table(); print("to_datetimes_strings", to_datetimes_strings)
    lastEntry = to_datetimes_strings.max()
    print ("Newest entry was:", lastEntry, end=" ")

    if maxdate:
        corrected = min(lastEntry, maxdate)
        if corrected!=lastEntry:
            print("BUT that cannot be (probably typo, or caused by '=NOW()'), as the file version was from '%s', so using that instead:" % maxdate, end="")
            lastEntry=corrected
    print()

    timestamp=lastEntry
    filename1=filestump % ("-" + timestamp)
    return filename1


def test_generate_filename_from_newest_entry_timestamp():
    for sheetID, range, zeitcolumn, maxdate in (("1RWUIqzwxRJ3OJ_MJ3zEkY2HITg3Y1QeAP1WQvSENcrM","A5:AU406", "Zeit",  "20200321_211500"),
                                                ("1Um3c1uPWrgdbrvmjUref367UnDi_Bt1_iZLehvsZd60", "A5:AU406", "Zeit", "20200624_214200"),
                                                ("1jOjcJO4ffIMvksZkQFupikbT-M7ppQgtjFHiW037wHc", "A4:T405",
                                                 "Zeit (Datum, Uhrzeit) (Man kann =JETZT() oder =NOW() benutzen", "20200318_215000"
                                       )):
        print("\n")
        df=download_sheet_table(sheetID=sheetID, table=("Haupt", range), reindex=None)
        print("downloaded: %s" % sheetID)
        fn=generate_filename_from_newest_entry_timestamp(df, zeitcolumn=zeitcolumn, maxdate=maxdate)
        print(fn)


def save_csv_twice(df, filestump=HAUPT_FILES):
    """
    name file 1 like the newest entry, for later processing
    name file 2 like always, to have the newest data always in the same file
    return whether file 1 existed, to tell whether to regenerate plots etc
    """

    filename1 = generate_filename_from_newest_entry_timestamp(df, filestump=filestump)

    existed = os.path.isfile(filename1)
    df.to_csv(filename1, index=False)
    print(filename1)
    filename2=filestump % ""
    df.to_csv(filename2, index=False)
    print(filename2)
    return existed, (filename1, filename2)


def get_master_sheet_haupt(sheetID=RISKLAYER_MASTER_SHEET):
    """
    download risklayer master sheet, process, and save twice.
    returns whether that timestamped file existed already.
    TODO: catch exceptions, then return False
    """
    df = download_sheet_table(sheetID=sheetID)
    existed, files = save_csv_twice(df)
    return not existed


def add_urls_column(df, hauptversion="v02"):
    """
    combines all web sources into one column, as list
    """
    # print (df.columns); exit()
    websources = QUELLEN_SPALTEN[hauptversion]
    df["urls"]= [sorted(list(set( [url
                            for url in urllist
                            if url!="" and url!="nn"] )))    # remove the nans
                 for urllist in df[websources].fillna("").values.tolist()]
    return df


def load_master_sheet_haupt(filestump=HAUPT_FILES, timestamp="-20200520_211500", hauptversion="v02"):
    """
    load the file.
    process master sheet, to supply page generating function
    with a column "urls" that is a list of data sources for each district
    while doing that, print some infos; for consistency checks.
    Also, make AGS into index.
    """
    filename =filestump % timestamp
    print ("Reading from", filename)
    df = pandas.read_csv(filename)
    daysum=df["Fälle Heute bis 00Uhr"].sum()
    print ("Sum", daysum, end=" ")
    lastEntry=pandas.to_datetime(df.Zeit).max()
    print ("Last entry was:", lastEntry)
    df=add_urls_column(df, hauptversion=hauptversion)
    print ("added urls column with all websources combined")

    df.index=df.AGS.tolist()
    print("index = AGS, for easier access")
    return df


################################### version history 'Haupt' sheets ##########################################

def idFromUrl(url):
    pos1=url.find("/d/")+3
    pos2=url.find("/", pos1)
    sheetId = url[pos1:pos2]
    return sheetId

def get_haupt_sheet_ids(sheet=VERSION_HISTORY_TABLE ):
    date2url = download_sheet_table(sheetID=sheet["sheetID"],
                                    table=(sheet["sheetName"], sheet["range"]), reindex=False)
    ids=[]
    for row in date2url.iterrows():
        url= row[1]["url"]
        sheetId = idFromUrl(url)
        ids.append(sheetId)

    date2url["id"] = ids
    date2url["dt"]=pandas.to_datetime(date2url.datetime, format="%d/%m/%Y %H:%M", errors='coerce')
    date2url.sort_values(by="dt", inplace=True) # , ascending=False)
    # pandas_settings_full_table(); print(date2url[["dt", "id", "range", "zeit"]])
    return date2url[["dt", "id", "range", "zeit"]]

def get_haupt_sheet_ids_then_download_all(sheet=VERSION_HISTORY_TABLE):

    sheets = get_haupt_sheet_ids(sheet=sheet)
    print ("Got the table of version history copy sheets, processing them now:")
    sys.stdout.flush()

    for _, row in sheets.iterrows():
        # download
        sheetID,dt,range,zeit = row["id"], row["dt"], row["range"], row["zeit"]
        print ("\n", dt,range,sheetID,zeit, end=" ... ")

        try:
            df = download_sheet_table(sheetID=sheetID, table=('Haupt', range), reindex=False)
        except pandas.errors.ParserError as e:
            print ("ERROR: %s %s" % (type(e), e))
            print ('Probably incorrect access rights. Press "Share", and switch to "Anyone on the Internet with this link can view",')
            print ("in this sheet: https://docs.google.com/spreadsheets/d/%s" %sheetID )
            continue

        # get newest 'Zeit' entry (OR use date from sheets-table) --> generate filename
        maxdate = dt.strftime("%Y%m%d_%H%M%S") # print(maxdate); exit()
        fn=generate_filename_from_newest_entry_timestamp(df, filestump=HAUPT_FILES, zeitcolumn=zeit, maxdate=maxdate)
        print("For CSV using filename:", fn)

        # save as csv to the data folder:
        if os.path.isfile(fn):
            print ("ALERT: file existed, overwriting it now.")
        df.to_csv(fn, index=False)
        sys.stdout.flush()


########################### web crawling ####################################################################

def get_wikipedia_landkreise_table(url='https://de.wikipedia.org/wiki/Liste_der_Landkreise_in_Deutschland',
                                   filename=WP_FILE):

    """
    scrape wikipedia page for districts information

    todo: the same for https://de.wikipedia.org/wiki/Liste_der_kreisfreien_St%C3%A4dte_in_Deutschland
    """

    print ("\nscrape wikipedia page:")

    columns=['AGS', 'Kreis', 'Kreis_WP', 'KreisSitz', 'KreisSitz_WP', 'Einwohner', 'Fläche', 'Karte']
    df = pd.DataFrame(columns=columns)

    f = requests.get(url).text
    soup = bs.BeautifulSoup(f, 'lxml')
    parsed_table = soup.find_all('table')[0]


    for row in parsed_table.find_all('tr'):
        cells = list(row.find_all('td'))
        if cells:
            AGS=list(cells[0].stripped_strings)[0]

            lk=(list(cells[1].stripped_strings))[0]
            lk_wp = cells[1].a['href']

            lk_hs= (list(cells[4].stripped_strings))[0]
            lk_hs_wp = cells[4].a['href']

            lk_ew = int((list(cells[5].stripped_strings))[0].replace(".", ""))

            lk_fl_de = (list(cells[6].stripped_strings))[0]
            lk_fl = float(lk_fl_de.replace(".", "").replace(".", "").replace(",", "."))

            lk_pic = cells[8].img['src']

            datarow = [AGS, lk, lk_wp, lk_hs, lk_hs_wp, lk_ew, lk_fl, lk_pic]
            df=df.append(pd.DataFrame([datarow], columns=columns))

    df.to_csv(filename, index=False)
    return df

def load_wikipedia_landkreise_table(filepath=WP_FILE):
    """
    load the wikipedia information
    """
    df = pd.read_csv(filepath, index_col="AGS")
    return df


def scrape_and_test_wikipedia_pages():
    get_wikipedia_landkreise_table();
    df=load_wikipedia_landkreise_table();
    print("\ndescribe:\n%s" % df.describe())
    print("\nsum:\n%s" % df[["Einwohner", "Fläche"]].sum().to_string())
    print("\nexample:\n %s" % df.loc[5370].to_string())
    return df


###############################################################################################


if __name__ == '__main__':
    # testing_swap_specific_typo_cells(); exit()
    # test_comparison(); exit()

    # get_master_sheet_haupt(); exit()  # my copy of 20/May
    # get_master_sheet_haupt(sheetID=RISKLAYER_MASTER_SHEET); exit() # their current state of the master sheet, might not work during daytime, too busy
    # haupt = load_master_sheet_haupt(timestamp=""); exit()

    # notEqual, ts = downloadData(andStore=False); exit()
    # newData, ts = downloadData(); print ("\ndownloaded timeseries CSV was new:", newData); exit()

    downloadData(); # exit()

    load_data(); exit()
    # ts, bnn = data(withSynthetic=True); # exit()
    # TODO: Use 'datacolumns' instead of dropping
    # print(); print (ts[ts["AGS"]=="00000"].drop(["AGS", "ADMIN"], axis=1).values.tolist()); exit()

    # df=scrape_and_test_wikipedia_pages(); print (df.to_string())

    # get_haupt_sheet_ids(); exit()
    # test_generate_filename_from_newest_entry_timestamp(); exit()
    # get_haupt_sheet_ids_then_download_all()
    pass
