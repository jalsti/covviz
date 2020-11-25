#!/usr/bin/env python3
"""
@summary: assemble pages from plots and tables, include external links, etc.

@version: v03.4 (24/June/2020)
@since:   27/April/2020

@author:  Dr Andreas Krueger
@see:     https://github.com/covh/covviz for updates

@status:  Needs: (cleanup, function comments, take large functions apart, refactor into SETTINGS.py,  etc.)
          See: todo.md for ideas what else to do. 
          NOT yet: pretty, easy to read. But it works.
"""


import os, datetime, math
import urllib.parse

import dataFiles, dataMangling, dataPlotting, districtDistances, dataTable



"""
https://www-ai.cs.tu-dortmund.de/COVID19/index.html#05370 Heinsberg
https://www-ai.cs.tu-dortmund.de/COVID19/index.html#16 Thüringen
"""
TU_DORTMUND='<a target="_blank" href="https://www-ai.cs.tu-dortmund.de/COVID19/index.html#%s">AI.CS.TU-Dortmund #AGS%s</a>'


                                # https://duckduckgo.com/?q=bautzen+AND+(corona+OR+covid19)&t=h_&df=w&ia=web
                                # https://duckduckgo.com/?q=(ammerland+OR+westerstede)+and+(corona+OR+covid19)&t=h_&df=w&ia=web
SEARCH_ENGINE = {"duckduckgo" : {"kreis" : "https://duckduckgo.com/?q=%s+AND+(corona+OR+covid19)&t=h_&df=w&ia=web",
                                "kreisUndSitz" : "https://duckduckgo.com/?q=(%s+OR+%s)+and+(corona+OR+covid19)&t=h_&df=w&ia=web"},
                            # https://duckduckgo.com/?q=bautzen+AND+(corona+OR+covid19)+%21g&t=h_&df=w&ia=web
                            # https://duckduckgo.com/?q=(ammerland+OR+westerstede)+and+(corona+OR+covid19)+%21g&t=h_&df=w&ia=web
                            # not the double %% for % encoding
                "google": {"kreis" : "https://duckduckgo.com/?q=%s+AND+(corona+OR+covid19)+%%21g&t=h_&df=w&ia=web",
                           "kreisUndSitz" : "https://duckduckgo.com/?q=(%s+OR+%s)+and+(corona+OR+covid19)+%%21g&t=h_&df=w&ia=web"}
                }


SPONSORS_IMG_LINK = """
<a href="https://github.com/sponsors/covh" target="_blank">
<img src="../pics/sponsor.gif" alt="sponsor me - credit card or paypal" title="sponsor me - credit card or paypal"></a> 
"""

SPONSORS_IMG_ABOUT_PAGE = """
<a href="about.html#support">
<img src="../pics/sponsor.gif" 
     alt=  "sponsor me - credit card / paypal, or cryptocurrencies" 
     title="sponsor me - credit card / paypal, or cryptocurrencies"
     style="top: 5px; right: 5px; position:fixed; z-index: 10;">
</a> 
"""

CHOICES_ITEMS_JS_STUB = """<span id="{choice_id}">
        <script>
            document.getElementById("{choice_id}").insertAdjacentHTML("afterbegin", 
            '<big>&rarr;</big>&nbsp;<a target="_blank" href="choice.html?cols={cols}&title={title}&loc={locs}">{linktext}</a><br>');
        </script>
        </span>"""

def search_URLs(kreis, kreissitz):
    text="search last week, "
    if kreis==kreissitz:
        text += kreis
    else:
        text += kreis +" OR " + kreissitz
    text += ": "
    links=[]
    for engine in ("duckduckgo", "google"):
        choices=SEARCH_ENGINE[engine]
        ulpqp=urllib.parse.quote_plus # if there are umlauts or whatever
        if kreis==kreissitz:
            url = choices["kreis"] % ulpqp(kreis)
        else:
            url = choices["kreisUndSitz"] % (ulpqp(kreis), ulpqp(kreissitz))
        links.append('<a href="%s" target="_blank">%s</a>' % (url, engine))
    text += ", ".join(links) 
    return text

def test_search_URLs():
    for kreis, kreissitz in (("kreis", "kreis"), ("kreis", "kreissitz")):
        print (search_URLs(kreis, kreissitz))
                             

def footerlink():
    text = '<hr><a href="https://covh.github.io/cov19de">tiny.cc/cov19de</a>'
    dt = ("%s" % datetime.datetime.now())[:19]
    text +=" page generated %s." % dt
    return text

def wikipedia_link(wp, AGS, base_url=dataFiles.WP_URL):
    text=""
    try:
        k=wp.loc[AGS]
        kreis, kreissitz = k["Kreis"], k["KreisSitz"]
    except:
        pass # the wikipedia table has only 294 rows while there are 401 districts
        kreis, kreissitz = None, None
    else:
        text += 'Wikipedia: Kreis <a target="_blank" href="%s%s">%s</a>'% (base_url, k["Kreis_WP"], k["Kreis"])
        text += ' Kreissitz <a target="_blank" href="%s%s">%s</a>'% (base_url, k["KreisSitz_WP"], k["KreisSitz"])
    return text, kreis, kreissitz 


def bundesland(fed, filename_HTML, dm: dataMangling.DataMangled, distances, cmap, km):
    page = dataTable.PAGE % fed.name
    district_AGSs = dm.ts_sorted[dm.ts_sorted.Bundesland==fed.name].index.tolist()
    
    page +='<a name="top">'
    page +='Up to <a href="about.html">about.html</a> or to overview of <a href="Deutschland.html">Germany</a>\n'
    page +='Or down to <a href="#Kreise">Kreise (districts)</a> ' + SPONSORS_IMG_ABOUT_PAGE
    flagimg = dataTable.flag_image(fed.name, fed.population, height=20)
    page +="<hr><h1>%s %s, and its %d districts (%s)</h1>\n" % (flagimg, fed.name, len(district_AGSs), dm.datacolumns[-1])
    page +='<img src="%s"/><p/>' % ("../pics/" + fed.filename)
    page += "population: {:,}".format(fed.population)
    page += " <big>&rarr;</big>&nbsp;current prevalence: {:.2f} known infected per 100,000 population (over all time).<br/> ".format(fed.prevalence_100k)
    page += "(The plot's background color gradient for a {singular} indicates how large its prevalence value is, " \
            "relative to all other {plural}; e.g. the less colourful the gradient is, " \
            "the less total cases per inhabitant exist (over all time), in relation to the maximum prevalence value over all {plural})." \
            "<br/>\n".format(singular="Bundesland (federal state)", plural="Bundeslaender (federal states)")

    # add table with rows for some plotted values
    date_columns_reversed = dm.datacolumns.tolist()
    date_columns_reversed.reverse()
    labels = ["total cases", "daily cases", "7&nbsp;days mean"]
    data = [fed.cumulative[::-1], fed.daily[::-1], fed.rolling_mean7.fillna('-').values.ravel().tolist()[::-1]]
    page += dataTable.plot_values_to_HTML_table(labels=labels, data_rows=data, date_columns=date_columns_reversed)
    # page +='total cases: <span style="color:#1E90FF; font-size:x-small;">%s</span><p/>\n' % fed.cumulative
    
    page +="<hr><h2 id='Kreise'>%s's %d Kreise</h2>\n" % (fed.name, len(district_AGSs))
    page +="<h3>Sorted by 'expectation day'</h3>\n"
    
    page +='Click on name of Kreis to see detailed data. If not all visible, '
    page +='<a href="javascript:expand_table_div(\'tablediv_kreise\');">expand table area</a>, or use scrollbar.<p/>\n'
    
    AGS_str_list = dm.ts_sorted[dm.ts_sorted.Bundesland==fed.name].index.astype('str').to_list()
    locs=",".join(AGS_str_list[:])
    page += CHOICES_ITEMS_JS_STUB.format(choice_id="all_district_plots", locs=locs, cols=4,
                                         title="covviz plots of all %d %s\\'s Kreise \(districts\), sorted by expectation day" % (len(AGS_str_list), fed.name),
                                         linktext="Open overview of (only) the plots of all %d %s\\'s Kreise \(districts\) in a new window." % (len(AGS_str_list), fed.name))


    districtsHTML = dataTable.Districts_to_HTML_table(dm, district_AGSs, cmap, filename=None,
                                                      rolling_window_size=5, header="\n", footer="\n")
    
    page+=districtsHTML[1]
    page +='<a href="#">Back to top</a> or: Up to <a href="about.html">about.html</a>\n'
    
    wp=dataFiles.load_wikipedia_landkreise_table()

    for AGS in district_AGSs:
        dstr: dataMangling.District = dataMangling.get_Kreis(AGS)

        try:
            nearby_links, nearby_AGS = districtDistances.kreis_nearby_links(dm.bnn, distances, AGS, km) if AGS else ""
        except ValueError:
            print(f"'{fed.name}' has no neighbours, ignoring it")
            continue

        anchor = "AGS" + dstr.AGS
        page +="<hr><h3 id=%s>%s AGS=%s</h3>\n" % (anchor, dstr.title, AGS)
        page +="Neighbours within %d km: %s<p/>\n" % (km, nearby_links)

        # add choices link of country, Bundesland, AGS and neighbors with JS (as work with JS only)
        locs = "Deutschland,"
        if dstr.name != fed.name:  # add Bundesland if not same as city
            locs += f"{fed.name},"
        locs += f"{AGS},{nearby_AGS}"
        cols = 3 # if nearby_AGS.count(',') < 12 else 4
        page += CHOICES_ITEMS_JS_STUB.format(choice_id=f"{anchor}_choice", locs=locs, cols=cols, title=f"covviz plots of {dstr.name} and neighbours within {km}km",
                                             linktext="Open all plots of these neighbours in a new window.")

        filename_kreis_PNG = "Kreis_" + ("00000"+str(AGS))[-5:] + ".png"

        page +='<img src="%s"/><p/>' % ("../pics/" + dstr.filename)
        
        page += ("%s %s" % (dstr.type_name, dstr.name)) + " population: {:,}".format(dstr.population)
        page += " <big>&rarr;</big>&nbsp;current prevalence: {:.2f} known infected per 100,000 population (over all time). ".format(dstr.prevalence_100k)
        page += "Weekly incident limits are "
        page += f"{dstr.weeklyIncidenceLimit1Per100k:.2f} ({dataMangling.WEEKLY_INCIDENCE_LIMIT1_PER_100K}'s limit), "
        page += f"{dstr.weeklyIncidenceLimit2Per100k:.2f} ({dataMangling.WEEKLY_INCIDENCE_LIMIT2_PER_100K}'s limit), "
        page += f"{dstr.weeklyIncidenceLimit3Per100k:.2f} ({dataMangling.WEEKLY_INCIDENCE_LIMIT3_PER_100K}'s limit). <br/>"
        page += "(The plot's background color gradient for a {singular} indicates how large its prevalence value is, " \
                "relative to all other {plural}; e.g. the less colourful the gradient is, " \
                "the less total cases per inhabitant exist (over all time), in relation to the maximum prevalence value over all {plural})." \
                "<br/>\n".format(singular="Kreis (district)", plural="Kreise (districts)")

        page += "sources: %s; " % dstr.sources
        page +='other sites: %s' % (TU_DORTMUND % (dstr.AGS, dstr.AGS) )
        wpl, kreis, kreissitz = wikipedia_link(wp, int(AGS))
        if wpl: 
            page +=', %s' % (wpl)
        else:
            kreis = kreissitz = dstr.name # we have that wikipedia info about kreissitz only for 294 out of 401, for remainder fall back to kreis name
        page += ", " + search_URLs(kreis, kreissitz)


        # add table with rows for some plotted values
        labels = ["total cases", "daily cases", "7&nbsp;day sum", "7&nbsp;day incid."]
        data = [dstr.cumulative[::-1], dstr.daily[::-1], dstr.incidence_sums[::-1], dstr.incidence_values[::-1]]
        page += dataTable.plot_values_to_HTML_table(labels=labels, data_rows=data, date_columns=date_columns_reversed)

        page += "<p/>"
        page +='<a href="#">Back to top</a> or: Up to <a href="about.html">about.html</a>\n'
    
    page += footerlink()
    page += dataTable.PAGE_END
    
    fn=os.path.join(dataFiles.PAGES_PATH, filename_HTML)
    with open(fn, "w") as f:
        f.write(page)
    
    return fn

def Bundeslaender_alle(dm: dataMangling.DataMangled, distances, cmap, km):
    print ("Creating HTML files for all 'Bundeslaender'")
    filenames, population = [], 0
    rootpath = os.path.abspath(dataFiles.REPO_PATH)
    Bundeslaender = dm.Bundeslaender_sorted
    for BL_name in Bundeslaender.index.tolist():
        if BL_name == "Deutschland":
            continue
        print (BL_name, end=" ")
        fed: dataMangling.CovidDataArea = dataMangling.get_BuLa(Bundeslaender, BL_name, dm.datacolumns)
        filename_HTML = fed.filename.replace(".png", ".html")
        filename_HTML = filename_HTML.replace("bundesland_", "")

        fn = bundesland(fed, filename_HTML, dm, distances, cmap, km)
        fn_abs = os.path.abspath(fn).replace(rootpath, "")
        
        filenames.append((BL_name, fn_abs ))
        population += fed.population
    print ("\nTotal population covered:", population)
    print ("%d filenames written: %s" % (len(filenames), filenames))
    
    return filenames
    
    
def Deutschland_simple(Bundeslaender_filenames, filename_HTML="Deutschland_simple.html"):
    page = dataTable.PAGE
    page +='<a name="#top">'
    page +='Up to <a href="about.html">about.html</a>\n'
    
    page +="<h1>Germany and its 16 countries</h1>\n"
    page +='<img src="%s"/><p/>' % ("../pics/Deutschland.png")
    page +="total cases: %s<br>\n" #  % (list(map(int, cumulative)))
    # prevalence = cumulative[-1] / pop_BL * 1000000
    # page += "population: {:,}".format(pop_BL)
    # page += " <big>&rarr;</big>&nbsp;current prevalence: %d known infected per 1 million population (over all time)<p/>\n" % (prevalence )
    
    page +="<h2>16 Bundesländer</h2>\n"
    
    page +="<ul>\n"
    for BL_name, BL_filename in Bundeslaender_filenames:
        print(BL_name, BL_filename)
        page += '<li><a href="%s">%s</a></li>\n' % (BL_filename,BL_name)
    
    page +="</ul>\n"
        
    page +="<p/>TODO: Insert long 401 districts table"
    fn=os.path.join(dataFiles.PAGES_PATH, filename_HTML)
    with open(fn, "w") as f:
        f.write(page)
    
    return fn
    
    
GOOGLESHEET_HTML="""

<hr><h3 id=googlesheet>401 Kreise - Ranked by MORTALITY</h3>
Note that the <b>old sorting by mortality</b> (how many deads per
1 million population) is now also linking every Kreis (district) to
this website here = so that is another way how the regions can be sorted. <br/>
Perhaps remember the --&gt; shortcut to
that googlesheet --&gt; <a href="http://tiny.cc/kreise">tiny.cc/kreise</a><p/>

(Screenshot below is not updated, so:) Click on the image to see a more recent <b>mortality sorting</b>.<p/> 
<div>
<a href="https://docs.google.com/spreadsheets/d/1KbNjq2OPsSRzmyDDidbXD4pcPnAPfY0SsS693duadLw/#gid=1644486167">
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
<img src="../pics/googlesheet-mortality-top-20200430.png"
     alt="table of Kreise sorted by mortality" border="0" width="100%" />
</a><br>
</div>
<br>
"""
# width="583" height="320"

def bloverview(Bundeslaender_sorted, ifPrint=False):
    print("\ngenerating overview of 16 Bundeslaender in Germany:")
    BLs = sorted(Bundeslaender_sorted.index.tolist())
    BLs = [BL for BL in BLs if BL not in ("Dummyland", "Deutschland")]

    class page(object):
        page = ""

        def a(self, t):
            self.page += t + "\n"

    p = page()
    for BL in BLs:
        print(BL)
        imgprop = 'src="../pics/bundesland_%s.png" alt="bundesland_%s.png"' % (BL, BL)
        p.a("<figure>")
        p.a('<a href="%s.html"><figcaption>%s</figcaption><img %s></a>' % (BL, BL, imgprop))
        p.a("</figure>")
    if ifPrint:
        print(p.page)
    return p.page


def Deutschland(dm: dataMangling.DataMangled, cmap, filename_HTML="Deutschland.html"):
    page = dataTable.PAGE % "Deutschland"
    page +='<a name="top">'
    page +='UP to <a href="about.html">about.html</a> \n'
    page +='| or DOWN to <a href="#Bundeslaender">16 Bundesländer</a>, or Bundesländer plots <a href="#Bundeslaender_4by4">alphabetically</a> or <a href="#Kreise">401 Kreise</a> '
    page +='or 401 Kreise sorted by <a href="#googlesheet">mortality</a> (googlesheet table). ' + SPONSORS_IMG_ABOUT_PAGE
    
    page +='<hr><h1 id="de">Germany</h1>\n' 
    page +='<img src="%s"/><p/>' % ("../pics/Deutschland.png")
    
    DE=dm.Bundeslaender_sorted.drop(["Deutschland", "Dummyland"], errors='ignore').sum() # errors='ignore' in case Dummyland is not part of the dataset anyways
    cumulative = DE[dm.datacolumns].astype(int).tolist()
    
    prevalence = cumulative[-1] / DE["Population"] * 100000.0
    page += "population: {:,}".format(DE["Population"])
    page += " <big>&rarr;</big>&nbsp;current prevalence: {:.2f} known infected per 100,000 population (over all time).<br/>\n".format(prevalence)

    page +='total cases: <span style="color:#1E90FF; font-size:x-small;">%s</span><p/>\n' % (list(map(int, cumulative)))

    
    page +='<hr><h2 id="Bundeslaender">16 Bundesländer</h2>\n'
    page +='<h3 id="Bundeslaender_expectationday">ranked by "expectation day"</h3>\n'
    page +="Click on Bundesland name to see detailed data.<p/>\n"
    
    fn, bulaHTML= dataTable.BuLas_to_HTML_table(dm, cmap, table_filename=None, rolling_window_size=3, header="\n", footer="\n")
    
    page+=bulaHTML
    
    page +='<a href="#">Back to top</a> or: Up to <a href="about.html">about.html</a>\n'
    
    page +='<hr><h3 id="Bundeslaender_4by4">Bundeslaender alphabetically</h3>\n'
    page += "(The plot's background color gradient for a {singular} indicates how large its prevalence value is, " \
            "relative to all other {plural}; e.g. the less colourful the gradient is, " \
            "the less total cases per inhabitant exist (over all time), in relation to the maximum prevalence value over all {plural})." \
            "<br/>\n".format(singular="Bundesland (federal state)", plural="Bundeslaender (federal states)")


    page += '<div class="bloverview">'
    page += bloverview(dm.Bundeslaender_sorted)
    page += '</div>'
    
    page +="<p style='clear:both'>Click on the image of a Bundesland to enter its page, with all its districts.</p>"
    page +='<a href="#">Back to top</a> or: Up to <a href="about.html">about.html</a>\n'
    
    
    page +='<hr><h2 id="Kreise">401 Kreise (districts)</h2>\n'
    page +='<h3>ranked by "expectation day" or other measures ...</h3>\n'
    page +="Click on name of Kreis (or Bundesland) to see detailed data. To see all of them, "
    page +='<a href="javascript:expand_table_div(\'tablediv_kreise\');">expand table area</a>, or use scrollbar.<p/>\n'

    AGS_str_list = dm.ts_sorted.index.astype('str').to_list()
    locs=",".join(AGS_str_list[:])
    page += CHOICES_ITEMS_JS_STUB.format(choice_id="all_district_plots", locs=locs, cols=4,
                                         title="covviz plots of all 401 german Kreise \(districts\), sorted by expectation day",
                                         linktext="Open overview of (only) the plots of all 401 german Kreise \(districts\) in a new window.")

    district_AGSs = dm.ts_sorted.index.tolist()
    fn, kreiseHTML = dataTable.Districts_to_HTML_table(dm, district_AGSs, cmap, filename="kreise_Germany.html", header="\n", footer="\n")
    page += kreiseHTML 
    
    page +='<a href="#">Back to top</a> or: Up to <a href="about.html">about.html</a>\n'

    page +=GOOGLESHEET_HTML
    page +='<a href="#">Back to top</a> or: Up to <a href="about.html">about.html</a>\n'

    
    page +=footerlink()
    
    page += dataTable.PAGE_END
    
    fn=os.path.join(dataFiles.PAGES_PATH, filename_HTML)
    with open(fn, "w") as f:
        f.write(page)
    
    return os.path.abspath(fn)


def neighbour_districts_table(neighbours, ifPrint=False):
    """
    takes neighbours dataframe with columns [title, img, link]
    create HTML table - square or rectangular
    returns HTML code 
    """
    
    N=len(neighbours)
    w=math.ceil(math.sqrt(N))
    h=math.ceil(N/w)
    print ("\nTable of %d elements, shape: %d x %d = which leaves %d cells empty." %(N, w, h, w*h-N), end="")
    print (" Generating html table, for overview of neighbouring districts:")
    
    c=0
    
    class page(object):
        page=""
        def a(self, t):
            self.page+=t+"\n"
           
    rows = list(neighbours.itertuples())
    p=page()
    p.a("<table>")
    for i in range(w):
        p.a("<tr>")
        for j in range(h):
            try:
                row = rows[c]
            except:
                p.a('<td></td>')
            else:
                # print (row)
                imgprop='src="%s" alt="%s" title="%s"'%(row.img, row.title, row.title)
                p.a('<td>%s<br/><a href="%s"><img %s width="366" height="214"/></a></td>' % (row.title, row.link, imgprop))
            c+=1
        p.a("</tr>")
    # p.a("<caption>test</caption>")
    p.a("</table>")
    if ifPrint:
        print (p.page)
    return p.page


def prepare_list_of_neighbour_districts(AGS, distances, km, bnn):
    """
    identify neighbours within distance km, 
    and create ["link", "title", "img"] information
    that then can be input for the HTML table
    
    returns a dataframe, with more columns
    """
    
    neighbours = districtDistances.nearby (distances, AGS, km).copy() # the .copy gets rid of the slice warning 
    neighbours.loc[-1, "AGS1"] = AGS
    neighbours.loc[-1, "AGS2"] = AGS
    neighbours.loc[-1, "km"] = 0
    neighbours.sort_values("km", ascending=True, inplace=True)
    # TODO: insert itself at km 0
    imgs, titles = [],[]
    for index, row in neighbours[["AGS2", "km"]].iterrows():
        AGS2 = int(row["AGS2"])
        #print (AGS2, row["km"])
        filename, nameAndType, link = districtDistances.kreis_link(bnn, AGS2)
        neighbours.loc[index, "link"] = filename
        filepath_kreis_PNG = "../pics/Kreis_" + ("00000"+str(AGS2))[-5:] + ".png"
        #print (filepath_kreis_PNG, filename, nameAndType, link )
        neighbours.loc[index, "img"] = filepath_kreis_PNG
        title = "%s (%.1f km)" % (nameAndType, row["km"])
        #print (title)
        neighbours.loc[index, "title"] = title
        # imgs += [filepath_kreis_PNG]
        # titles += [title]
    # print (neighbours)
    # neighbours["img"]=imgs
    # neighbours["title"]=titles
    
    #print (neighbours.to_string())
    return neighbours
    


SIMPLEPAGE="""

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

</STYLE>
<link href="https://fonts.googleapis.com/css?family=Roboto+Condensed&display=swap" rel="stylesheet">

</head>
<body>
"""
 
SIMPLEPAGE_END="""
</body>
</html>
"""


def neighbour_districts_table_page(AGS, distances, km, bnn):
    """
    select neighbours within distance km=...
    create additional columns, as prep for table
    make HTML table, square or rectangular
    write page to HTML file
    """
    neighbours = prepare_list_of_neighbour_districts(AGS, distances, km, bnn)
    table = neighbour_districts_table(neighbours)

    gen, bez, _,_ = dataMangling.AGS_to_population(bnn, AGS)
    _, nameAndType, _= districtDistances.kreis_link(bnn, AGS)
    
    page = SIMPLEPAGE % ("%s (%s) neighbours" % (gen, bez)) 
    page = page. replace('onload="scroll_rightmost()"', '')
    page += table
    page += '<p>All plots are regenerated with new data every night. Beware this temporary <a href="hotspots.html">hotspot</a> is an experimental page - it might get removed, so please do not link to it. Instead link to project <a href="http://tiny.cc/cov19de">http://tiny.cc/cov19de</a>.</p>'
    page += SIMPLEPAGE_END
    # print (page)
    AGS_5digits = ("00000"+str(AGS))[-5:]
    filename = os.path.join(dataFiles.PAGES_PATH, "kreis_%s_plus_%skm.html" % (AGS_5digits, km))
    with open(filename, "w") as f:
        f.write(page)
    print (filename)
    return filename


def generate_hotspot_files():
    
    dm = dataMangling.dataMangled(ifPrint=False)
    distances = districtDistances.load_distances()
    print ("50 km, relative threshold; or absolute threshold, and not already among relative threshold:")
    for AGS in (5558, 16072, 9163, 16076, 9473, 9263, 9278, 8231, 4011, 5382, 9362, 9478, 5370, 3459, 9463, 9376, 9475, 5554, 8231,
                4012, 3352, 16052, 9473, 7315, 3159, 9771, 5754, 3361, 15003, 5570, 3103, 6632, 3458, 3401, 5170, 5111, 5915, 5112,
                9188, 9279, 7334, 9173,5366,5158,7312, 11000, 5112, 3241, 9162, 5913, 4011, 5315, 6412, 9761, 5958, 
                16055, 1051, 5122, 3460, 8128, 7232, 5113, 2000, 5911, 8136, 5562):
        neighbour_districts_table_page(AGS=AGS, distances=distances, km=50, bnn=dm.bnn)
    
    print ("\n100 km:")
    for AGS in (5754,):
        neighbour_districts_table_page(AGS=AGS, distances=distances, km=100, bnn=dm.bnn)
    print ("\n150 km")
    for AGS in ():
        neighbour_districts_table_page(AGS=AGS, distances=distances, km=150, bnn=dm.bnn)



if __name__ == '__main__':
    
    # generate_hotspot_files(); exit()
    
    # test_search_URLs(); exit()
    
    # haupt = dataFiles.load_master_sheet_haupt(timestamp="") # timestamp="" means newest
    dm = dataMangling.dataMangled(haupt=None)
    # fourbyfour(Bundeslaender_sorted); exit()
    distances = districtDistances.load_distances()

    print()
    print()
    cmap = dataTable.colormap()
    # print ( bundesland("Hessen", "bundesland_Hessen.png", "Hessen", 7777, [8,9,10], "Hessen.html", ts, ts_sorted, datacolumns, bnn, distances, cmap, 50) ); exit()
    # print ( bundesland("Saarland", "bundesland_Saarland.png", "Saarland", 7777, [8,9,10], "Saarland.html", ts, ts_sorted, datacolumns, bnn, distances, cmap, 50) ); exit()

    Bundeslaender_filenames = Bundeslaender_alle(dm, distances, cmap, km=50)
    print (Bundeslaender_filenames)
    # Bundeslaender_filenames = [('Brandenburg', '../data/../pages/Brandenburg.html'), ('Bremen', '../data/../pages/Bremen.html'), ('Thüringen', '../data/../pages/Thüringen.html'), ('Bayern', '../data/../pages/Bayern.html'), ('Saarland', '../data/../pages/Saarland.html'), ('Hessen', '../data/../pages/Hessen.html'), ('Schleswig-Holstein', '../data/../pages/Schleswig-Holstein.html'), ('Baden-Württemberg', '../data/../pages/Baden-Württemberg.html'), ('Niedersachsen', '../data/../pages/Niedersachsen.html'), ('Sachsen-Anhalt', '../data/../pages/Sachsen-Anhalt.html'), ('Sachsen', '../data/../pages/Sachsen.html'), ('Hamburg', '../data/../pages/Hamburg.html'), ('Berlin', '../data/../pages/Berlin.html'), ('Rheinland-Pfalz', '../data/../pages/Rheinland-Pfalz.html'), ('Nordrhein-Westfalen', '../data/../pages/Nordrhein-Westfalen.html'), ('Mecklenburg-Vorpommern', '../data/../pages/Mecklenburg-Vorpommern.html'), ('Dummyland', '../data/../pages/Dummyland.html')]
    # Deutschland_simple(Bundeslaender_filenames)
    
    fn=Deutschland(dm, cmap)
    print ("\n" + fn)
    
    
