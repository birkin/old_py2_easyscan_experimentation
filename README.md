overview
--------

Code to improve the process of requesting a scan for items at the [Annex](http://library.brown.edu/about/annex/), the Library's offsite storage facility.

The current system involves multiple steps and is confusing.


basic flow
----------

- javascript (part of this app) is called by [Josiah](http://josiah.brown.edu) (our [ILS](http://en.wikipedia.org/wiki/Integrated_library_system) catalog) that creates a 'Request Scan' link next to each item at the Annex that:
    - is available
    - is not in special collections
- that link contains an item-barcode (needed by the Annex inventory-control software) and some additional item info
- clicking the link will take the user to this app
- _note: though the javascript piece is specifically for Josiah, our [VuFind](http://library.brown.edu/find/Discover/Results) and coming [Blacklight](https://github.com/projectblacklight/blacklight/wiki) interfaces will be able to easily link to this app_
- after authenticating, the user fills out chapter/title and page-range citation info
- the user clicks 'Submit Scan Request', then sees a confirmation message, and receives a confirmation email
- behind the scenes the request is formatted for the Annex inventory-control-system's software, and transmitted -- done!


urls & params
-------------

- The root `scheme://host/easyscan` will redirect to the info page at `scheme://host/easyscan/info/`
- The root request url: `scheme://host/easyscan/request`
- A typical url may look like: `scheme://host/easyscan/request?callnumber=BF173.A2%20A5&barcode=31236090031116&title=American%20imago&bibnum=null&volume_year=53%20(1996)`
- required params
    - `barcode` -- this is the item barcode -- will be sent to the Annex
- optional params
    - `bibnum` -- used to look up title for landing-page display if title-param is null; not sent to Annex
    - `callnumber` -- simply presented to user at landing-page; not sent to Annex
    - `title` -- the bib title; presented to user at landing page; is sent to Annex
    - `volume_year` -- simply presented to user at landing-page; not sent to Annex

Important future note...

- `bibnum` will become a required parameter; it will be used to validate the format of the item


contacts
--------

- birkin_diana at brown dot edu
- jean_rainwater at brown dot edu

---
