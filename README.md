[![Build Status](https://travis-ci.org/OCA/connector-interfaces.svg?branch=7.0)](https://travis-ci.org/OCA/connector-interfaces)
[![Coverage Status](https://coveralls.io/repos/OCA/connector-interfaces/badge.png?branch=7.0)](https://coveralls.io/r/OCA/connector-interfaces?branch=7.0)

# Connector Interfaces

This repository provides various projects using the ![Odoo Connector Framework](https://github.com/OCA/connector) for generic purposes, such as importing from data files or from external databases. 

# About OCA

This project is part of the ![Odoo Community Association](http://odoo-community.org) projects.
=======



File Repository
-----------------
File management parameters definition (location, protocol, access)
to connect towards file storage places (external or internal)
allow to define protocol with external repository (FTP, SFTP, File system)

File Document
---------------
Manage and store files used to exchange datas (import/export)
with any external applications (file exchange or web services)
Example : logistics centers, e-commerce platforms, automated machines

File Email
-------------
Importing and processing the attachment of an email.
The attachment of the email will be imported
as a file_document and then in your custom module you can process it.
An example of processing can be found in
[account_statement_email](http://bazaar.launchpad.net/~akretion-team/banking-addons/bank-statement-reconcile-7.0-file-exchange/view/head:/account_statement_email/fetchmail.py)
