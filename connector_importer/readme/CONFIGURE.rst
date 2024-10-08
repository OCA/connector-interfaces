
Import type
~~~~~~~~~~~

Import types are the main configuration of the import.
They describe which models you want to import and how to import them.

Exaple of configuration::

    <record id="import_type_product_product_all_in_one" model="import.type">
        <field name="name">Import Product - all in one</field>
        <field name="key">product_product_all_in_one</field>
        <field name="options">

    - model: product.product
        options:
            importer:
                odoo_unique_key: barcode
            mapper:
                name: product.product.mapper

    - model: res.partner
        options:
            importer:
                odoo_unique_key: name
            override_existing: false
            mapper:
                name: importer.mapper.dynamic
                source_key_prefix: supplier.
                source_key_whitelist: supplier.name
                default_keys:
                    supplier_rank: 1

    - model: product.supplierinfo
        options:
            importer:
                odoo_unique_key: name
            mapper:
                name: product.supplierinfo.mapper
                source_key_prefix: supplier.

        </field>

    </record>

In this example we have 3 models to import one after the other using the same source file:

* product.product
* res.partner
* product.supplierinfo

The import will run in the order of the configuration: first product.product, then res.partner and finally product.supplierinfo.
For each model we have a configuration that describes how to import the data.
With the ``options`` key we can define the configuration of the import for each component: ``importer``, ``mapper``, ``record_handler``, ``tracking_handler``.

The are 4 main components in the import configuration:

* importer
* mapper
* record_handler
* tracking_handler

Each of them is responsible for a specific part of the import.

The importer
~~~~~~~~~~~~

``importer`` is the main component that will import the data. It will use the ``mapper`` to map the data from the source to the destination model.
If no ``name`` is defined the importer will use the default importer for the model which is capable of importing any model.
Most of the time you don't need a specific importer.

As the importer is the main component of the import if you want to customize it you'll have to declare it at an higher level, next to the ``options`` key::

    - model: product.product
        importer:
            name: product.product.importer
        options:
            mapper:
                name: product.product.mapper

The importer accepts the following options:

* ``odoo_unique_key``: the field that will be used to find the record in Odoo. If the record is found it will be updated, otherwise it will be created.

    NOTE: the value in the column declared as ``odoo_unique_key`` will be treated as xid only if the name of the column is ``ìd`` or if it starts with ``xid::``.

* ``break_on_error``: if set to True the import will stop if an error occurs. Default is False.
* ``override_existing``: if set to True the existing records will be updated. Default is True.
* ``translation_key_sep``: the separator used to split the translation key. Default is ``:``. See below for information about translation keys.
* ``translation_use_regional_lang``: if set to True the importer will use the regional language, eg: `fr_CH` vs `fr`.
* ``ctx``: a dictionary of values to inject in the context of the import.
* ``write_only``: if set to True the importer will not create new records, it will only update existing ones. Default is False.


The mapper
~~~~~~~~~~

The mapper is the component that will map the data from the source to the destination model.

The most flexible mapper is the ``importer.mapper.dynamic`` that will map the data based on the model introspection and some options that you can define.
The dynamic mapper accepts the following options:

* ``name``: the name of the mapper to use. If no name is defined the default mapper for the model will be used.
* ``source_key_prefix``: a prefix to add to the source key. This is useful when you want to map the same source key to different destination fields.
* ``source_key_whitelist``: a list of source keys to import. If not defined all the keys will be imported.
* ``source_key_blacklist``: a list of source keys to exclude from the import.
* ``source_key_rename``: a dictionary of source keys to rename. The key is the source key and the value is the new key.
* ``default_keys``: a dictionary of default values to set on the destination record. The key is the field name and the value is the default value.
* ``translation_keys``: a list of keys that will be used to translate the data. See below for information about translation keys.
* ``required_keys``: a list of keys that are required. If one of the keys is missing the record will be skipped. Please refer to the documentation of the mapper to see advanced options.

Considering the example above::

    - model: product.product
        options:
            mapper:
                name: importer.mapper.dynamic
                source_key_prefix: supplier.
                source_key_whitelist: supplier.name
                default_keys:
                    supplier_rank: 1

The mapper will:

* import only keys starting with ``supplier.`` ignoring the rest
* import only the key ``supplier.name``
* set the default value of ``supplier_rank`` to 1

The record_handler
~~~~~~~~~~~~~~~~~~

The record handler is the component that will handle the record create or update in Odoo.
This component is responsible for:

* finding the record in Odoo
* creating the record if not found
* updating the record if found
* handling the translations

If no ``name`` is defined the importer will use the default record handler for the model which is capable of handling any model.
If you want to customize the record handler you'll have to declare it at an higher level, next to the ``options`` key::

    - model: product.product
        options:
            record_handler:
                name: product.product.record_handler

To find the record in Odoo the record handler will use the ``odoo_unique_key`` if defined in the importer otherwise it will fallback to the matching domain. See below.

The record handler accepts the following options:

* ``name``: the name of the record handler to use. If no name is defined the default record handler for the model will be used.
* ``match_domain``: a domain to match the record in Odoo. When no odoo_unique_key is provided by the importer you must provide a match_domain.

    This key accepts a snippet returning a domain. The snippet will be evaluated in the context of the import and will receive:

    * ``orig_values``: the values from the source
    * ``values``: values computed by the mapper for the record
    * ``env``
    * ``user``
    * ``datetime``
    * ``dateutil``
    * ``time``
    * ``ref_id``: a function to get a record ID from a reference
    * ``ref``: a function to get a record from a reference

        Example::

            match_domain: |
                [('name', '=', values.get('name'))]

* ``must_generate_xmlid``: if set to True the importer will generate an XML ID for the record. Default is True if the unique key is an xmlid.
* ``skip_fields_unchanged``: if set to True the importer will skip the fields that are unchanged. Default is False.


Translations
~~~~~~~~~~~~

The importer can translate the data using the translation keys. The translation keys are a list of keys (column) that will be handled as translatable.
Whenever a key is found in the translation keys the importer will look for a column with the same name suffixed by the language code (eg: name:fr_CH).
If the column is found the importer will translate the data using the language code as context.
