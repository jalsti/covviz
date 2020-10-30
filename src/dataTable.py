#!/usr/bin/env python3
"""
@summary: HTML table with heatmap, inspired by Tomas Pueyo 

@version: v03.4 (24/June/2020)
@since:   25/April/2020

@author:  Dr Andreas Krueger
@see:     https://github.com/covh/covviz for updates

@status:  Needs: (cleanup, function comments, HTML template into separate file, etc.)
          PERHAPS: abstract table generator, so both (Kreise, Bundesländer) get generated by same routine?
          See: todo.md for ideas what else to do.
          NOT yet: ready, clearly structured, pretty, easy to read! But it works.
"""

import os

import pandas
import numpy
import matplotlib


import dataFiles, dataMangling, districtDistances
from dataMangling import bulaLink


def toHTMLRow(frame, row_index, datacolumns, cmap, labels, rolling_window_size=7):
    row = frame[datacolumns].loc[row_index].astype('int')
    # return row

    window=rolling_window_size
    rolling_mean_cum = row.rolling(window=window, center=True).mean()

    diff_rolling_mean = pandas.DataFrame(rolling_mean_cum).diff(axis=0).clip(lower=0)[row_index].tolist()
    diffmax = numpy.nanmax(diff_rolling_mean)
    
    row = row.iloc[::-1]
    diff_rolling_mean.reverse()

    cumulative=row.tolist()
    line="<tr>"

    for label in labels:
        line+="<td>%s</td>" % label

    for c, d in zip(cumulative, diff_rolling_mean):
        #                                    avoid extreme colors, shifted towards red: 0.30-0.80
        rgb = matplotlib.colors.to_hex(cmap( 0.30+(d/diffmax)*0.50 ))
        
        line+='<td bgcolor="%s"><span>%d</span></td> ' % (rgb, c)
        
    for label in labels:
        line+="<td>%s</td>" % label
        
    return line + "</tr>"
    


PAGE="""

<!DOCTYPE html>
<html lang="en">
<head>
<TITLE>%s</TITLE>
<STYLE>

table {
  border-collapse: collapse;
}

body {
  font-family: 'Roboto', sans-serif;
}


th, td {
  text-align:center;
  font-family: 'Roboto Condensed', sans-serif;
}

td span
{
  font-family: 'Teko', sans-serif;
  text-align:center;
}

th
{
  vertical-align: middle;
  text-align: center;
  border: 1px solid black;
  min-width: 18px;
}

th span
{
  -ms-writing-mode: tb-rl;
  -webkit-writing-mode: vertical-rl;
  writing-mode: vertical-rl;
  transform: rotate(180deg);
  white-space: nowrap;
  font-family: sans-serif;
}

.flag 
{
    border:1px solid #777777;
}

.tablearea {
    overflow-y: scroll;
    overflow-x: scroll;
    width: 100%%;
    max-height: 670px;
    display: inline-block;
}

.bloverview {
    display: flex;
    justify-content: space-evenly;
    flex-wrap: wrap;
}

.bloverview figcaption{
    text-align: center;
}

.bloverview figure{
    display: inline-block;
    margin-inline-start: 0px;
    margin-inline-end: 0px;
}

.bloverview img{
    width: 300px; /* should allow 4 images in a row on 1280 screen resolution */
}

// fix header row:
.tableFixHead          { overflow-y: auto; height: 100px; }
.tableFixHead th { position: sticky; top: 0; background-color: white; }
      
// fix borders:
// .tableFixHead,.tableFixHead td {   box-shadow: inset 1px -1px #000; }
      
.tableFixHead th {  box-shadow: inset 1px 1px #000, 0 1px #000; }

      

</STYLE>
<link href="https://fonts.googleapis.com/css?family=Roboto+Condensed|Teko&display=swap" rel="stylesheet">

</head>
<body>
"""

# It is a best practice to put JavaScript <script> tags 
# just before the closing </body> tag 
# rather than in the <head> section of your HTML. 
# The reason for this is that HTML loads from top to bottom. 
# The head loads first, then the body, and then everything inside the body.

# FIXME: that JS table sorting seems to be a bubble sort with directly manipulating the existing huge DOM on each switch.
#  (Maybe we should insert some timeouts on each switch step, as the only thinkable possibility to get it even slower. ;-))
PAGE_END="""
<script type="text/javascript" src="sort-table.js"></script>
</body>
</html>
"""

def flag_image(name, population=None, height=14):
    fn = "../pics/flag_%s.svg" % name
    info_str = name
    info_str  += " population={:,}".format(population) if population else ""
    text = '<img class="flag" height=%d src="%s" alt="%s" title="%s"/>' % (height, fn, fn, info_str)
    return text


def prevalence(datatable, row_index, datacolumns, population):
    cumulative = datatable[datacolumns].loc[row_index].astype('int')
    prev1mio = cumulative[-1] / population * 1000000
    return prev1mio


ATTRIBUTION = """<span style="color:#aaaaaa; font-size:x-small;">Source data from "Risklayer GmbH (www.risklayer.com) and Center for Disaster Management and Risk Reduction Technology (CEDIM) at Karlsruhe Institute of Technology (KIT) and the Risklayer-CEDIM SARS-CoV-2 Crowdsourcing Contributors". Data sources can be found under https://docs.google.com/spreadsheets/d/1wg-s4_Lz2Stil6spQEYFdZaBEp8nWW26gVyfHqvcl8s/edit?usp=sharing Authors: James Daniell| Johannes Brand| Andreas Schaefer and the Risklayer-CEDIM SARS-CoV-2 Crowdsourcing Contributors through Risklayer GmbH and Center for Disaster Management and Risk Reduction Technology (CEDIM) at the Karlsruhe Institute of Technology (KIT).</span><p/>""" 


def Districts_to_HTML_table(dm, district_AGSs, cmap, filename="kreise_Germany.html", rolling_window_size=3, header=PAGE % "Deutschland Kreise", footer=PAGE_END, divEnveloped=True):

    # total_max_cum, digits = maxdata(ts_sorted)
    
    tid="table_districts"
    page = header 
    if divEnveloped:
        page+= '<div class="tablearea" id="tablediv_kreise">'
    page+= '<table id="%s" class="tableFixHead">\n' % tid
    caption="Click on column header name, to sort by that column; click again for other direction."
    page += '<caption id="caption_kreise" style="text-align:right;">%s</caption>\n' % caption
    page +="<tr>"

    dc_head = dm.datacolumns.tolist()
    dc_head.reverse()

    colcount=len(dm.datacolumns)
    # print (datacolumns, colcount); exit()
    cols = [("total cases", True),
            ("7days new cases", True),
            ("Kreis", True),
            ("Prev. p.1mio", True),
            ("7days Incid.p.1mio", True),
            # ("7days Incid.p.1mio", True),
            ("Population", True),
            ("expectation day", True),
            ("Reff_4_7", True),
            ("Bundesland", True),
            ("info", False) ] 

    for i, col in enumerate(cols):
        colName, sorting = col
        if sorting:
            cellid = "\'%shc%d\'" % (tid, i)
            page += '<th onclick="sortTable(\'%s\', %d, %s)" id=%s>%s</th>' % (tid, i, cellid, cellid, colName)
        else:
            page += '<th>%s</th>' % (colName)

    for col in dc_head:
        page += "<th><span>%s</span></th>" % col

    page +="</tr>"
    
    for AGS in district_AGSs:
        dstr = dataMangling.get_Kreis(AGS)
        # print (AGS)
        # nearby_links = districtDistances.kreis_nearby_links(bnn, distances, AGS, km) if AGS else ""
        labels=[]
        
        # Add the last data column once more, so that table is sortable by that column:
        totalCases = dstr.total
        labels += ['%d' % totalCases]
        
        labels += ['%d' % dstr.new_last7days]
        labels += [dstr.link]
        labels += ["%d" % dstr.prevalence_1mio]
        labels += ['%d' % dstr.incidence_sum7_1mio]
        labels += ['{:,}'.format(dstr.population)]
        labels += ["%.1f" % dstr.center]
        labels += ["%.2f" % dstr.reff_4_7]
        labels += [bulaLink(dstr.fed_states_name)]
        labels += [flag_image(dstr.fed_states_name, dstr.fed_states__population)]
        # labels += [nearby_links]
        page += toHTMLRow(dm.ts_sorted, int(AGS), dm.datacolumns, cmap, labels, rolling_window_size=rolling_window_size) + "\n"
        
    page += "</table>"
    if divEnveloped:
        page += "</div>" 
    page += ATTRIBUTION + footer
    
    fn=None
    if filename:
        fn=os.path.join(dataFiles.PAGES_PATH, filename)
        with open(fn, "w") as f:
            f.write(page)
    
    return fn, page
    

def BuLas_to_HTML_table(dm: dataMangling.DataMangled, cmap, table_filename="bundeslaender_Germany.html", rolling_window_size=3, header = PAGE % "Bundeslaender", footer=PAGE_END, divEnveloped=True):

    # total_max_cum, digits = maxdata(ts_sorted)
    Bundeslaender= dm.Bundeslaender_sorted
    BL_names = Bundeslaender.index.tolist()

    tid="table_bundeslaender"
    page = header
    if divEnveloped:
        page += '<div class="tablearea" id="tablediv_bundeslaender">' 
    page += '<table id="%s" class="tableFixHead">\n' % tid
    caption="Click on column header name, to sort by that column; click again for other direction."
    page += '<caption style="text-align:right;">%s</caption>' % caption
    page +="<tr>"

    dc_head = dm.datacolumns.tolist()
    dc_head.reverse()

    cols = ["7days new cases", "Bundesland", "info", "Prev. p.1mio", "7days Incid.p.1mio", "Population", "expectation day", "Reff_4_7" ]

    for i, colName in enumerate(cols):
        cellid = "\'%shc%d\'" % (tid, i)
        page += '<th onclick="sortTable(\'%s\', %d, %s)" id=%s>%s</th>' % (tid, i, cellid, cellid, colName)

    for col in dc_head:
        page += "<th><span>%s</span></th>" % col

    page +="</tr>"

    for name_BL in BL_names:
        labels=[]
        fed = dataMangling.get_BuLa(Bundeslaender, name_BL, dm.datacolumns)
        labels += ['%d' % fed.new_last7days]
        labels += [fed.link]
        labels += [flag_image(name_BL)]
        labels += ["%d" % fed.prevalence_1mio]
        labels += ['%d' % fed.incidence_sum7_1mio]
        labels += ['{:,}'.format(fed.population)]
        labels += ["%.2f" % fed.center]
        labels += ["%.2f" % fed.reff_4_7]
        page += toHTMLRow(Bundeslaender, name_BL, dm.datacolumns, cmap, labels, rolling_window_size=rolling_window_size) + "\n"
        
    page += "</table>"
    if divEnveloped:
        page +=" </div>" 
    page += ATTRIBUTION + footer
    
    fn=None
    if table_filename:
        fn=os.path.join(dataFiles.PAGES_PATH, table_filename)
        with open(fn, "w") as f:
            f.write(page)

    return fn, page
    
def colormap():
    # cmap=plt.get_cmap("Wistia")
    # cmap=plt.get_cmap("summer")
    
    """
    # too dark:
    import matplotlib.colors as mcolors
    cdict = {'red':   ((0.0, 0.0, 0.0),
                       (0.5, 0.0, 0.0),
                       (1.0, 1.0, 1.0)),
             'blue':  ((0.0, 0.0, 0.0),
                       (1.0, 0.0, 0.0)),
             'green': ((0.0, 0.0, 1.0),
                       (0.5, 0.0, 0.0),
                       (1.0, 0.0, 0.0))}
    cmap = mcolors.LinearSegmentedColormap('my_colormap', cdict, 100)
    """
    # cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green","yellow","red"])
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["green","yellow","red"])
    
    cmap.set_bad("white")
    return cmap


if __name__ == '__main__':

    dm = dataMangling.dataMangled()

    AGS = 1001
    AGS = 5370
    print ( dm.ts_sorted["centerday"][AGS] )

    cmap = colormap()  
    
    print ( toHTMLRow(dm.ts_sorted, AGS, dm.datacolumns, cmap, labels=["%s" % AGS]) )

    district_AGSs = [1001, 1002, 5370, 9377]
    district_AGSs = dm.ts_sorted.index.tolist()
    
    distances = districtDistances.load_distances()
    print (Districts_to_HTML_table(dm, district_AGSs, cmap, divEnveloped=False)[0])
    
    # Bundeslaender.loc['Deutschland'] = Bundeslaender.sum().values.tolist()
    
    # print (BuLas_to_HTML_table(Bundeslaender_sorted, datacolumns, Bundeslaender_sorted.index.tolist(), cmap, divEnveloped=False)[0])
