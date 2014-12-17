overview
--------

Code to improve the process of requesting a scan for items at the Annex, Brown's offsite book storage facility.

The current system involves multiple steps and is confusing.


basic flow
----------

- javascript (part of this app) is called by Josiah (our III catalog) that creates a 'Request Scan' link next to each item at the Annex that:
    - is available
    - is not in special collections
- that link will contain barcode and some item info
- clicking the link will take the user to this app
- after authenticating, the user will be asked to add any additional citation info that has not been captured
- the user clicks 'Submit Scan Request' and receives a confirmation message
- behind the scenes the request is formatted for the Annex inventory-control-system's software, and transmitted


contacts
--------

birkin_diana at brown dot edu
jean_rainwater at brown dot edu

---
