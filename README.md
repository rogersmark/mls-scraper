mls-scraper
===========

Scraper of the MLS (soccer) site's statistics since they don't like to share. 
So far this is mostly a proof of concept, however if you'd like to try it, it 
does actually work. All you need to do is point it at a post game stats summary
found on MLSSoccer.com. For example, see this [Fire vs Columbus Recap](http://www.mlssoccer.com/matchcenter/2013-04-20-CHI-v-CLB/stats).

This script relies on:

* requests
* beautifulsoup
* mock

Just run like so:

    python mls_scraper.py http://www.mlssoccer.com/matchcenter/2013-04-20-CHI-v-CLB/stats

If you'd like to store the data this retrieves, I recommend taking a look at
my [mls-api](https://github.com/f4nt/mls-api) project.
