# covid19 time series visualization - districts of Germany
generates a static website from daily updated infections data in Germany.

---
## About this *covviz* fork
(see below next line for original README)

Most of the code in this repository (https://github.com/jalsti/covviz/) has originally been written, or is based on code written by Dr. Andreas Krüger, who published it at https://github.com/covh/covviz/. It got forked to make some tweaks to the graph plots, starting in September 2020 with a visible x-y–grid (which needed some changes to the x-/y-scaling/tick amount), faster generating times through using more than one CPU core, if available, fixing code for some opendatasoft data source changes, making plotting available with headless systems, and a more flexible district overview plotting setup, with similar setup for the [choice.html](https://jalsti.github.io/cov19de/pages/choice.html), which has now links for setting more (or less) columns in its overview, and to which a link gets added on the district plots, showing the plots of the cities in a 50km area around it on one page.

* The plotting of the daily cases got changed, with a new main graph to reflect the sum of the daily cases of the last 7 days for a date in a district, with showing the incidence borders for it.
* A color gradient on the plot backgrounds indicate how large the numbers in it get, compared to other plots of same type. Less colourfull means less relative total cases per people

Still most real work horse code is left in its original form, which is also the reason that all the links which point to the original project are left like they are.

And here now comes the original README of *covviz*:

---

### start here, to learn about the purpose of the project

[index.html](https://covh.github.io/cov19de/index.html) and then [pages/about.html](https://covh.github.io/cov19de/pages/about.html)

## architecture:
* covh/covviz = code. Python, bash scripts, instructions, static pages, etc = sparse, small, lots of .gitignore.
* covh/cov19de = site. Copies of all (generated & static) HTML pages, plot images, etc = the github pages at [covh.github.io/cov19de](https://covh.github.io/cov19de)  

If you want to work with this, and make your own copy of the site, fork both repositories. Swap out `covh` for your username everywhere below.

### dependencies, clone, install
needed machine wide dependencies: git for github, virtualenv for python, expect for unbuffer

    sudo apt install git python3-venv expect 

(IF you may not install software, but have git & venv installed already - you can ignore expect, and remove the `unbuffer` command later)

clone both repos, they MUST be besides each other, then enter the code repo 'covviz':
```
mkdir covh
cd covh
git clone https://github.com/covh/covviz.git
git clone https://github.com/covh/cov19de.git

cd covviz
```

virtual env with the *proven* dependencies versions given in requirements.txt
```
python3 -m venv ./py3science
source ./py3science/bin/activate
pip3 install -U pip wheel
pip install -r requirements.txt
ipython kernel install --user --name="py3science"
```

OR try the *newest* versions of the Python dependencies (also helps if your system has an **older version of Python**) :
```
deactivate
rm -r ./py3science
python3 -m venv ./py3science
source ./py3science/bin/activate
pip3 install -U pip wheel
pip3 install jupyter ipykernel numpy pandas matplotlib wget geopy requests beautifulsoup4 lxml bottle
ipython kernel install --user --name="py3science"
```
but no guarantees then that my code will still work.

### execute
first time: important! downloads districts GPS positions, generates pairwise distances, creates all pages and pics once:

    ./scripts/initialize.sh

later: pull code & site; recreate site, copy content into cov19de repo, git-add-commit-push, done. 

    ./scripts/downloadAndUpdate.sh
    
That script also shows some initial insights into the newest data already.

#### git push
git push (the last step of `downloadAndUpdate.sh`) will only properly work if you have write access to the repo, i.e. you must adapt the following to *your fork* of that repo (for example, swap out `covh` for *your* github username), and you must create and [upload an SSH key, see here](https://github.com/settings/keys), then edit the `.git config` of your site repo fork: 

    nano covh/cov19de/.git/config

and change it so that it contains something like this:

```
...
[remote "origin"]
	url = git@github.com:covh/cov19de.git
	...
...
[user]
    name = Your Name
    email = your@email.address
```

Run this simple script (after editing any file in that repo) in the site repo, to try out whether the ssh git push works:

[./git-add-commit-push.sh](https://github.com/covh/cov19de/blob/master/git-add-commit-push.sh)

If it does, your last step is to configure the github pages, in YOUR fork of https://github.com/covh/cov19de/settings (i.e. with `covh` changed to your username), to "Source master branch = Your GitHub Pages site is currently being built from the master branch."

**Done**.

Perhaps you want to also sync the timezone on that machine, so that the plots show German time: `sudo timedatectl set-timezone Europe/Berlin`.


## source data

> Data can be used for reproduction with attribution to "Risklayer GmbH (www.risklayer.com) and Center for Disaster Management and Risk Reduction Technology (CEDIM) at Karlsruhe Institute of Technology (KIT) and the Risklayer-CEDIM SARS-CoV-2 Crowdsourcing Contributors".  
> Data sources can be found under https://docs.google.com/spreadsheets/d/1wg-s4_Lz2Stil6spQEYFdZaBEp8nWW26gVyfHqvcl8s/edit?usp=sharing  
> Authors: James Daniell| Johannes Brand| Andreas Schaefer and the Risklayer-CEDIM SARS-CoV-2 Crowdsourcing Contributors through Risklayer GmbH and Center for Disaster Management and Risk Reduction Technology (CEDIM) at the Karlsruhe Institute of Technology (KIT). 

### initial dataset - but not uptodate
When initializing a new machine, it was just simpler to have an initial dataset available. Thus, I have now checked in the `26.05.2020` state of the risklayer source data (as it overrides the `.gitignore`, with forced `git add -f GermanyValues_RiskLayer.csv`). BUT I don't want to always update this repo when there is a -daily- new column. And a command is supposed to help with that. So ... I suggest you do that manually:

    git update-index --assume-unchanged data/GermanyValues_RiskLayer.csv

(the undoing would be `--no-assume-unchanged`).


### interactive notebook - runs Python in your browser!

experimental: 

* first try working with the raw data: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/covh/covviz/master?filepath=notebooks%2Frisklayer-pandas.ipynb) (starts a Jupyter notebook, with the whole repo preloaded, all dependencies installed, etc.).

## interactive app
This is experimental. Deployed to heroku with these commands:

```
heroku login --interactive

heroku create cov19de
heroku apps
heroku git:remote -a cov19de
git remote -v

git push heroku master # this is later enough to update the heroku app with newer code
heroku open
heroku logs --tail
```

or run locally with

```
source ./py3science/bin/activate
python3 src/app.py
```

## see also:

[todo.md](todo.md), [history.txt](history.txt), [log.txt](log.txt)

