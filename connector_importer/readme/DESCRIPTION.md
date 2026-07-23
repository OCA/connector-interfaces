This module allows to import / update records from files using the connector
framework and job queue.

To run an import you need at least:

* a backend, hosts the global configuration of the import.
* a recordset, hosts the configuration of the import for specific models and source
* a source, provides the data to import
* an import type, describes which models you want to import and how to import them
