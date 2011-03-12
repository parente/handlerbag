==========
handlerbag
==========

:Author: Peter Parente
:Description: A little layer on top of the Tornado web server to manage a bag of dynamic handlers.

Requirements
============

* `Tornado <http://github..com/facebook/tornado>`_
* `watchdog <http://github.com/gorakhargosh/watchdog>`_ (for the rstpages handler)

Use
===

#. Edit users.py and make yourself an admin
#. Run handlerbag.py
#. Visit http://localhost:5000/admin

Run handlerbag.py --help on the server for options like choosing a port.

License
=======

Copyright (c) 2010, 2011 Peter Parente. All Rights Reserved.

http://creativecommons.org/licenses/BSD/
