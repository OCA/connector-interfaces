# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
"""Provides various date/datetime helper"""
import datetime
import pytz
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


def convert_to_utc_datetime_with_tz(datetime_str):
    """Convert a naive Odoo datetime string
    into a :py:class:`datetime.datetime` with utc time zone

    :param datetime_str: Odoo datetime string
    :type datetime_str: str

    :return: return a datetime with tz correspnding to string parameter
    :trype: `datetime.datetime`
    """
    d_time = datetime.datetime.strptime(datetime_str,
                                        DEFAULT_SERVER_DATETIME_FORMAT)
    return pytz.utc.localize(d_time)
