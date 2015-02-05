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


contacts
--------

- birkin_diana at brown dot edu
- jean_rainwater at brown dot edu

---
