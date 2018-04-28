# -*- coding: utf-8 -*-
# flake8: noqa
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013 Camptocamp SA
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
# automatically captured data
"""Serialize data to mock SQL"""
import datetime
from collections import namedtuple
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

DummRecord = namedtuple('mega_code_table', 'mg_name, mg_code, mg_desc, x_date, x_datetime, create_time, modify_time')

sql_data = {
    ('SELECTcodeFROM(SELECTmg_codeAScode,mg_createTimeascreate_time,mg_modifyTimeasmodify_timeFROMmega_code_tableWHEREstatus=?)src_table', ('Active',)): [('1',), ('2',), ('3',), ('4',), ('5',)],

    ('SELECT*,mg_createTimeascreate_time,mg_modifyTimeasmodify_timeFROMmega_code_tableWHEREmg_codeIN(?,?,?,?,?)', ('2', '1', '3', '4', '5')): [DummRecord('name 2', '2', 'blablabla',
                                                                                                                                                          datetime.datetime(2010, 01, 01),
                                                                                                                                                          datetime.datetime(2011, 01, 01),
                                                                                                                                                          datetime.datetime(2010, 01, 01),
                                                                                                                                                          datetime.datetime(2011, 01, 01)),
                                                                                                                                               DummRecord('name 1', '1', 'blablabla',
                                                                                                                                                          datetime.datetime(2010, 01, 01),
                                                                                                                                                          datetime.datetime(2011, 01, 01),
                                                                                                                                                          datetime.datetime(2010, 01, 01),
                                                                                                                                                          datetime.datetime(2011, 01, 01)),
                                                                                                                                               DummRecord('name 3', '3', 'blablabla',
                                                                                                                                                          datetime.datetime(2010, 01, 01),
                                                                                                                                                          datetime.datetime(2011, 01, 01),
                                                                                                                                                          datetime.datetime(2010, 01, 01),
                                                                                                                                                          datetime.datetime(2011, 01, 01)),
                                                                                                                                               DummRecord('name 4', '4', 'blablabla',
                                                                                                                                                          datetime.datetime(2010, 01, 01),
                                                                                                                                                          datetime.datetime(2011, 01, 01),
                                                                                                                                                          datetime.datetime(2010, 01, 01),
                                                                                                                                                          datetime.datetime(2011, 01, 01)),
                                                                                                                                               DummRecord('name 5', '5', 'blablabla',
                                                                                                                                                          datetime.datetime(2010, 01, 01),
                                                                                                                                                          datetime.datetime(2011, 01, 01),
                                                                                                                                                          datetime.datetime(2010, 01, 01),
                                                                                                                                                          datetime.datetime(2011, 01, 01)),
                                                                                                                                               ]

}
