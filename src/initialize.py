#!/usr/bin/env python3
"""
@summary: initializes the repo, e.g. when started for the first time on a new machine 

@version: v03.4 (24/June/2020)
@since:   22/May/2020

@author:  Dr Andreas Krueger
@see:     https://github.com/covh/covviz for updates

@status:  more or less ready, doesn't need attention
"""

import daily, districtDistances, dataFiles, dataPages

def do_it(a=True, b=True, c=True, d=True):
    """
    some of this is very time consuming, so selectively switch it off when experimenting
    """
    
    if a:
        districtDistances.downloadFromOpendatasoft_and_generatePairwiseDistancesFile()
    
    if b:
        dataFiles.scrape_and_test_wikipedia_pages()

    if c:
        dataPages.generate_hotspot_files()
    
    if d:
        daily.daily_update(publish=False,
                           regenerate_pages_regardless_if_new_data=True,
                           regenerate_plots_regardless_if_new_data=True,
                           showExtremes=False,
                           withSyntheticData=False)

if __name__ == '__main__':
    
    do_it()
    # do_it(a=False, d=False)
   
    print ("\nREADY.")
    