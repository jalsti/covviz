#!/usr/bin/env python3
"""
@summary: download newest data, visual inspection, (if new) generate plots & pages, copy into webfacing repo, git push

@version: v03.4 (24/June/2020)
@since:   28/April/2020

@author:  Dr Andreas Krueger
@see:     https://github.com/covh/covviz for updates

@status:  needs: (cleanup, function comments, refactoring into other .py files, solve/record TODOs, etc.)
          not yet: ready, clearly structured, pretty, easy to read. But it works.
"""

import os, datetime, shutil, subprocess

import dataFiles, dataMangling, dataPlotting, districtDistances, dataTable, dataPages
from dataFiles import PICS_PATH, PAGES_PATH, WWW_REPO_PICS, WWW_REPO_PAGES, WWW_REPO_PATH, WWW_REPO_PATH_GIT_SCRIPT, REPO_PATH, ALSO_TO_BE_COPIED

# TODO: move the following (up to showSomeExtremeValues()) into some dataRanking perhaps?
# also make HTML tables from it.

def columns_into_integers(ts_sorted, datacolumns):
    """
    todo: migrate this to dataMangling, and adapt to / test with Bundeslaender
    also do some many tests, to see that all is still good then. 
    """
    ts_sorted["new_last14days"]=ts_sorted["new_last14days"].astype(int)
    ts_sorted["new_last7days"]=ts_sorted["new_last7days"].astype(int)
    for datecol in datacolumns:
        ts_sorted[datecol]=ts_sorted[datecol].astype(int)
        
    
def add_incidence_prevalence(ts_sorted, datacolumns):
    """
    TODO: can probably also go into dataMangling?
    """
    ts_sorted["incidence_1mio_last14days"]=1000000*ts_sorted["new_last14days"]/ts_sorted["Population"]
    ts_sorted["incidence_1mio_last7days"] =1000000*ts_sorted["new_last7days"]/ts_sorted["Population"]
    ts_sorted["prevalence_1mio"]=1000000*ts_sorted[datacolumns[-1]]/ts_sorted["Population"]


def add_daily(ts_sorted, datacolumns):
    ts_sorted["new cases"] = ts_sorted[datacolumns[-1]] - ts_sorted[datacolumns[-2]]
    
COLUMN_ORDER = ["prevalence_1mio", "new cases", "new_last7days", "incidence_1mio_last7days", "new_last14days", "incidence_1mio_last14days", "centerday", "Reff_4_7_last"]
    
def newColOrder(df, datacolumns, firstColumns=["ADMIN", "Population", "Bundesland"]):
    cols = list(df.columns.values)
    # print(cols)
    # print (type(datacolumns.tolist()))
    cNew= firstColumns + datacolumns.tolist() + COLUMN_ORDER
    diffcols = list(set(cols) - set(cNew))
    if diffcols:
        print ("Forgotten these columns, adding them:", diffcols)
    cNew += diffcols
    return df[cNew]


# TODO: move this elsewhere:

   
def title(text):
    sep="*"*len(text+" * *")
    return "\n%s\n* %s *\n%s" %(sep, text, sep)

def showSomeExtremeValues(ts_sorted, datacolumns, n=15):
    columns_into_integers(ts_sorted, datacolumns)
    add_incidence_prevalence(ts_sorted, datacolumns)
    add_daily(ts_sorted, datacolumns)
    ts_sorted = newColOrder(ts_sorted, datacolumns)

    for col in ("new cases", "incidence_1mio_last7days", "incidence_1mio_last14days", "Reff_4_7_last"):
        print(title("sorted by    %s   descending:" % col))
        ts_sorted.sort_values(col, ascending=False, inplace=True) 
        print (ts_sorted.drop(datacolumns[:-2], axis=1).head(n=n).to_string( float_format='%.1f'))
        
    # raise Exception("Simulated Error")
    
    
def showBundeslaenderRanked(Bundeslaender_sorted, datacolumns, rankedBy="incidence_1mio_last7days"):
    print(title("Bundesländer ranked by '%s':" % rankedBy))
    columns_into_integers(Bundeslaender_sorted, datacolumns)
    add_incidence_prevalence(Bundeslaender_sorted, datacolumns)
    add_daily(Bundeslaender_sorted, datacolumns)
    #Bundeslaender_sorted["Bundesland"]=Bundeslaender_sorted.index
    Bundeslaender_sorted = newColOrder(Bundeslaender_sorted , datacolumns, firstColumns=["Population"]) # ["Bundesland"])
    Bundeslaender_sorted.sort_values(rankedBy, ascending=False, inplace=True)
    print (Bundeslaender_sorted.drop(datacolumns[:-5], axis=1).to_string( float_format='%.2f'))
    
    
def loadAndShowSomeExtremeValues():
    print ("\n show some insights\n")
    ts, bnn, ts_sorted, Bundeslaender_sorted, dates, datacolumns = dataMangling.dataMangled(withSynthetic=True) 
    # print (ts_sorted.columns)
    
    showSomeExtremeValues(ts_sorted, datacolumns)
    showBundeslaenderRanked(Bundeslaender_sorted, datacolumns)

## download and process:

def download_all(showExtremes=True):
    new_CSV, _ = dataFiles.downloadData()
    print ("\ndownloaded timeseries CSV was new: %s \n" % new_CSV)

    new_master_state = dataFiles.get_master_sheet_haupt(sheetID=dataFiles.RISKLAYER_MASTER_SHEET);
    print ("\ndownloaded mastersheet has new state: %s \n" % new_master_state)
    
    if showExtremes:
        loadAndShowSomeExtremeValues()
    
    return new_CSV, new_master_state 
    

def generate_all_pages(withSyntheticData=True):
    
    ts, bnn, ts_sorted, Bundeslaender_sorted, dates, datacolumns = dataMangling.dataMangled(withSynthetic=withSyntheticData)
    print()

    distances = districtDistances.load_distances()
    cmap = dataTable.colormap()
    
    haupt = dataFiles.load_master_sheet_haupt(timestamp="") # timestamp="" means newest
    print()
    Bundeslaender_filenames = dataPages.Bundeslaender_alle(Bundeslaender_sorted, ts, ts_sorted, datacolumns, bnn, distances, cmap, km=50, haupt=haupt);
    print (Bundeslaender_filenames)
    
    fn = dataPages.Deutschland(Bundeslaender_sorted, datacolumns, cmap, ts_sorted, bnn )
    print ("\n" + fn)
    
    return True
    

def generate_all_plots(withSyntheticData=False):

    ts, bnn, ts_sorted, Bundeslaender_sorted, dates, datacolumns = dataMangling.dataMangled(withSynthetic=withSyntheticData)
    print()

    print ("Plotting takes a bit of time. Patience please. Thanks.")
    done = dataPlotting.plot_all_Bundeslaender(ts, bnn, dates, datacolumns, ifPrint=False)
    print ("plot_all_Bundeslaender: %d items" % len(done))
    
    listOfAGSs = ts["AGS"].tolist()
    print ("Plotting %d images, for each Kreis. Patience please: " % len(listOfAGSs))
    done = dataPlotting.plot_Kreise_parallel(ts, bnn, dates, datacolumns, listOfAGSs, ifPrint=True)
    print ("plot_Kreise done: %d items" % len(done))
    print()

    return True


def copy_all():
    print (os.getcwd()) 
    fromTo = [[PICS_PATH, WWW_REPO_PICS], 
              [PAGES_PATH, WWW_REPO_PAGES]]
    for s, d in fromTo:
        try:
            # this was responsible for the site disappearing when using 2nd machine.
            # eventually it is good though, so instead once run 'scripts/initialize.sh'
            shutil.rmtree(d)
        except:  
            pass # ignore error if folder did not exist
        dst = shutil.copytree(s, d)
        print (dst)
        os.remove(os.path.join(d, ".gitignore"))

    for single_file in ALSO_TO_BE_COPIED:
        dst = shutil.copy(os.path.join(REPO_PATH, single_file), WWW_REPO_PATH)
        print (dst)
    
    return True
    
def git_commit_and_push(path=WWW_REPO_PATH, script=WWW_REPO_PATH_GIT_SCRIPT):
    print ("\ngit script '%s' please be patient ..." % script)
    try:
        before = os.getcwd()
        os.chdir(path)
        answer = subprocess.check_output([script], shell=True)
    except Exception as e:
        print ("git ERROR:", type(e), e)
        return False
    else:
        print (answer.decode("utf-8"))
        return True
    finally: 
        os.chdir(before)


def daily_update(regenerate_pages_regardless_if_new_data=False, regenerate_plots_regardless_if_new_data=False, publish=True, showExtremes=True, withSyntheticData=False):
    print ("Started at", ("%s" % datetime.datetime.now()) [:19],"\n")
    
    success1, success2, success3, success4, success5  = False, False, False, False, False
    
    print ("Downloading risklayer data:")
    # new_CSV, new_master_state = True, True
    new_CSV, new_master_state = download_all(showExtremes=showExtremes)
    success1 = True

    line = "\n" + ("*"*50) + "\n"
        
    if new_CSV or regenerate_pages_regardless_if_new_data:
        success2 = generate_all_pages(withSyntheticData=withSyntheticData)
    else:
        print (line+"ALERT: no new pages generated"+line)
        
    if not regenerate_plots_regardless_if_new_data and not new_CSV:
        print (line+"ALERT: no new plots generated"+line)
    else:
        success3 = generate_all_plots()
        
    if publish: 
        success4 = copy_all()
            
        if success4:
            print ()
            success5 = git_commit_and_push()
            print ("git push:" + ("successful" if success5 else "not successful"))
            
    print ("\ndownload data: %s, regenerate pages: %s, regenerate plots: %s, copy: %s, git push: %s" % (success1, success2, success3, success4, success5))
    
    print ("Finished at", ("%s" % datetime.datetime.now()) [:19],"\n")
    
    


if __name__ == '__main__':
    
    # git_commit_and_push(); exit()
    
    # loadAndShowSomeExtremeValues(); exit()
    daily_update(publish=False, withSyntheticData=False); exit()
    # daily_update(regenerate_pages_regardless_if_new_data=True, withSyntheticData=False); exit()
    
    daily_update()
    
    loadAndShowSomeExtremeValues()
    
    print ("\nREADY.")
