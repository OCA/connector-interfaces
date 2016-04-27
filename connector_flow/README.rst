.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Connector-Flow
==============

This module provides a minimal framework for common
data import/export tasks based on the OpenERP Connector. Tasks like parsing
and writing a CSV file or uploading a file to an FTP server can be chained
into task flows.

At the moment every flow must a have a unique start. One task can trigger
several tasks.

The module adds a new menu item "Import/Export" under the Connector top-level
menu where tasks and task flows can be configured. Tasks can be run from
the "Run Task" wizard. If a task needs a file as input, a file can be uploaded
in the wizard.

The *connector_flow_example_{ftp,product}* modules provide pre-configured
demo flows.

This module was definitely inspired by the works of Akretion (file_repository)
and Camptocamp (connector_file).

A very brief tutorial can be found at http://blog.initos.com/?p=1220


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/connector-interfaces/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/connector-interfaces/issues/new?body=module:%20connector_flow%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Thomas Rehn <thomas.rehn@initos.com>
* Peter Hahn <peter.hahn@initos.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
