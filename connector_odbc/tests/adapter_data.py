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
import datetime
from collections import namedtuple
DummRecord = namedtuple('mega_code_table', 'mg_name, mg_code, mg_desc, x_date, x_datetime, create_time, modify_time')
simulated_mega_table = {
    ('mega_code_table', 'search', (('date', False),)): ['1', '2', '3', '4', '5'],

    ('mega_code_table', 'read', ('1', '2', '3', '4', '5')): [DummRecord('name 2', '2', 'blablabla',
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
                                                                        datetime.datetime(2011, 01, 01))],
    ('mega_code_table', 'search', (('date', '2012-06-01 00:00:00'),)): ['1'],

    ('mega_code_table', 'read', ('1',)): [DummRecord('name 1', '1', 'comment updated',
                                                     datetime.datetime(2010, 01, 01),
                                                     datetime.datetime(2011, 01, 01),
                                                     datetime.datetime(2010, 01, 01),
                                                     datetime.datetime.today())],
    ('mega_code_table', 'missing', (u'1', u'2', u'3', u'4', u'5')): [],
    ('mega_code_table', 'read', ('3',)): [],
    ('mega_code_table', 'search', (('date', '2012-06-03 00:00:00'),)): ['1', '2', '3', '4'],
    ('mega_code_table', 'read', ('1', '2', '3', '4')): [DummRecord('name 2', '2', 'blablabla',
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
                                                                   datetime.datetime(2011, 01, 01))],
    ('mega_code_table', 'missing', (u'1', u'2', u'3', u'4')): ['3'],

}
