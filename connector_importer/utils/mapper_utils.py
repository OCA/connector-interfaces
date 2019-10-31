# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

import pytz

from odoo import fields

from ..log import logger

FMTS = ("%d/%m/%Y",)

FMTS_DT = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.000")


def to_date(value, formats=FMTS):
    """Convert date strings to odoo format."""

    for fmt in formats:
        try:
            value = datetime.strptime(value, fmt).date()
            break
        except ValueError:
            pass
    if not isinstance(value, str):
        try:
            return fields.Date.to_string(value)
        except ValueError:
            pass
    # the value has not been converted,
    # maybe because is like 00/00/0000
    # or in another bad format
    return None


def to_utc_datetime(orig_value, tz="Europe/Rome"):
    """Convert date strings to odoo format respecting TZ."""
    value = orig_value
    local_tz = pytz.timezone("Europe/Rome")
    for fmt in FMTS_DT:
        try:
            naive = datetime.strptime(orig_value, fmt)
            local_dt = local_tz.localize(naive, is_dst=None)
            value = local_dt.astimezone(pytz.utc)
            break
        except ValueError:
            pass
    if not isinstance(value, str):
        return fields.Datetime.to_string(value)
    # the value has not been converted,
    # maybe because is like 00/00/0000
    # or in another bad format
    return None


def to_safe_float(value):
    """Safely convert to float."""
    if isinstance(value, float):
        return value
    if not value:
        return 0.0
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return 0.0


def to_safe_int(value):
    """Safely convert to integer."""
    if isinstance(value, int):
        return value
    if not value:
        return 0
    try:
        return int(value.replace(",", "").replace(".", ""))
    except ValueError:
        return 0


CONV_MAPPING = {
    "date": to_date,
    "utc_date": to_utc_datetime,
    "safe_float": to_safe_float,
    "safe_int": to_safe_int,
}


def convert(field, conv_type, fallback_field=None, pre_value_handler=None, **kw):
    """ Convert the source field to a defined ``conv_type``
        (ex. str) before returning it.
        You can also use predefined converters like 'date'.
        Use ``fallback_field`` to provide a field of the same type
        to be used in case the base field has no value.
    """
    if conv_type in CONV_MAPPING:
        conv_type = CONV_MAPPING[conv_type]

    def modifier(self, record, to_attr):
        if field not in record:
            # be gentle
            logger.warn("Field `%s` missing in line `%s`", field, record["_line_nr"])
            return None
        value = record.get(field)
        if not value and fallback_field:
            value = record[fallback_field]
        if pre_value_handler:
            value = pre_value_handler(value)
        # do not use `if not value` otherwise you override all zero values
        if value is None:
            return None
        return conv_type(value, **kw)

    return modifier


def from_mapping(field, mapping, default_value=None):
    """ Convert the source value using a ``mapping`` of values.
    """

    def modifier(self, record, to_attr):
        value = record.get(field)
        return mapping.get(value, default_value)

    return modifier


def concat(field, separator=" ", handler=None):
    """Concatenate values from different fields."""

    # TODO: `field` is actually a list of fields.
    # `field` attribute is required ATM by the base connector mapper and
    # `_direct_source_field_name` raises and error if you don't specify it.
    # Check if we can get rid of it.

    def modifier(self, record, to_attr):
        value = [
            record.get(_field, "") for _field in field if record.get(_field, "").strip()
        ]
        return separator.join(value)

    return modifier


def xmlid_to_rel(field):
    """ Convert xmlids source values to ids.
    """

    def modifier(self, record, to_attr):
        value = record.get(field)
        if value is None:
            return None
        if isinstance(value, str):
            # m2o
            rec = self.env.ref(value, raise_if_not_found=False)
            if rec:
                return rec.id
            return None
        # x2m
        return [
            (6, 0, self.env.ref(x).ids)
            for x in value
            if self.env.ref(x, raise_if_not_found=False)
        ]

    return modifier


# TODO: consider to move this to mapper base klass
# to ease maintanability and override


def backend_to_rel(  # noqa: C901
    field,
    search_field=None,
    search_operator=None,
    value_handler=None,
    default_search_value=None,
    default_search_field=None,
    search_value_handler=None,
    allowed_length=None,
    create_missing=False,
    create_missing_handler=None,
):
    """A modifier intended to be used on the ``direct`` mappings.

    Example::

        direct = [(backend_to_rel('country',
                    search_field='code',
                    default_search_value='IT',
                    allowed_length=2), 'country_id'),]

    :param field: name of the source field in the record
    :param search_field: name of the field to be used for searching
    :param search_operator: operator to be used for searching
    :param value_handler: a function to manipulate the raw value
        before using it. You can use it to strip out none values
        that are not none, like '0' instead of an empty string.
    :param default_search_value: if the value is none you can provide
        a default value to look up
    :param default_search_field: if the value is none you can provide
        a different field to look up for the default value
    :param search_value_handler: a callable to use
        to manipulate value before searching
    :param allowed_length: enforce a check on the search_value length
    :param create_missing: create a new record if not found
    :param create_missing_handler: provide an handler
        for getting new values for a new record to be created.
    """

    def modifier(self, record, to_attr):
        search_value = record.get(field)

        if search_value and value_handler:
            search_value = value_handler(self, record, search_value)

        # handle defaults if no search value here
        if not search_value and default_search_value:
            search_value = default_search_value
            if default_search_field:
                modifier.search_field = default_search_field

        # get the real column and the model
        column = self.model._fields[to_attr]
        rel_model = self.env[column.comodel_name].with_context(active_test=False)

        if allowed_length and len(search_value) != allowed_length:
            return None

        # alter search value if handler is given
        if search_value and search_value_handler:
            search_value = search_value_handler(search_value)

        if not search_value:
            return None

        search_operator = "="
        if column.type.endswith("2many"):
            # we need multiple values
            search_operator = "in"
            if not isinstance(search_value, (list, tuple)):
                search_value = [search_value]

        if modifier.search_operator:
            # override by param
            search_operator = modifier.search_operator

        # finally search it
        search_args = [(modifier.search_field, search_operator, search_value)]

        value = rel_model.search(search_args)

        if (
            column.type.endswith("2many")
            and isinstance(search_value, (list, tuple))
            and not len(search_value) == len(value or [])
        ):
            # make sure we consider all the values and related records
            # that we pass here.
            # If one of them is missing we have to create them all before.
            # If `create_missing_handler` is given, it must make sure
            # to create all the missing records and return existing ones too.
            # Typical use case is: product categories.
            # If we pass ['Categ1', 'Categ2', 'Categ3'] we want them all,
            # and if any of them is missing we might want to create them
            # using a `create_missing_handler`.
            value = None

        # create if missing
        if not value and create_missing:
            try:
                if create_missing_handler:
                    value = create_missing_handler(self, rel_model, record)
                else:
                    value = rel_model.create({"name": record[field]})
            except Exception as e:
                msg = (
                    "`backend_to_rel` failed creation. "
                    "[model: %s] [line: %s] [to_attr: %s] "
                    "Error: %s"
                )
                logger.error(msg, rel_model._name, record["_line_nr"], to_attr, str(e))
                # raise error to make importer's savepoint ctx manager catch it
                raise

        # handle the final value based on col type
        if value:
            if column.type == "many2one":
                value = value[0].id
            if column.type in ("one2many", "many2many"):
                value = [(6, 0, [x.id for x in value])]
        else:
            return None

        return value

    # use method attributes to not mess up the variables' scope.
    # If we change the var inside modifier, without this trick
    # you get UnboundLocalError, as the variable was never defined.
    # Trick tnx to http://stackoverflow.com/a/27910553/647924
    modifier.search_field = search_field or "name"
    modifier.search_operator = search_operator or None

    return modifier
