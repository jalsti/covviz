#!/usr/bin/env python3
"""
@summary: download newest data, visual inspection, (if new) generate plots & pages, copy into webfacing repo, git push 

@version: v03.4 (24/June/2020)
@since:   22/May/2020

@author:  Dr Andreas Krueger
@see:     https://github.com/covh/covviz for updates

@status:  more or less ready, does NOT need attention.
"""


import daily

if __name__ == '__main__':
    
    daily.daily_update(publish=True, showExtremes=True, withSyntheticData=False)
    
    # daily.showSomeExtremeValues()
    
    print ("\nREADY.")
