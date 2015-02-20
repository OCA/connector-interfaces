# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2015 Camptocamp SA
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
import types
import datetime
import pytz
from mock import MagicMock
from .common import CommonTest, mock_simple_salesforce
from ..lib.date_convertion import convert_to_utc_datetime
from ..unit.rest_api_adapter import SalesforceRestAdapter, error_handler
from ..unit.exceptions import (SalesforceSessionExpiredError,
                               SalesforceRESTAPIError,
                               SalesforceResponseError,
                               SalesforceSecurityError)
try:
    from simple_salesforce import (SalesforceAuthenticationFailed,
                                   SalesforceExpiredSession,
                                   SalesforceGeneralError)
except ImportError:
    pass


class SalesforceRestAdapterTest(CommonTest):

    def get_adapter(self):
        conn_env = self.get_connector_env(self.model_name)
        return conn_env.get_connector_unit(SalesforceRestAdapter)

    def setUp(self):
        super(SalesforceRestAdapterTest, self).setUp()
        self.model_name = 'connector.salesforce.account'

    def test_datetime_converter(self):
        """test date utils"""
        naive_date = '2015-12-31 00:00:00'
        utc_date = convert_to_utc_datetime(naive_date)
        self.assertEqual(
            datetime.datetime(2015, 12, 31, 0, 0, tzinfo=pytz.utc),
            utc_date
        )

    def test_get_updated_no_date(self):
        """Test the get_updated function of the adapter"""
        response = MagicMock(name="get_updated")
        response.side_effect = [{'records': [{'Id': 'uuid_01'}]}]
        with mock_simple_salesforce(response):
            adapter = self.get_adapter()
            result = adapter.get_updated()
        self.assertIsInstance(result, types.GeneratorType)
        self.assertEqual(list(result), ['uuid_01'])

    def test_get_updated_date(self):
        """Test the get_updated function of the adapter"""
        response = MagicMock(name="get_updated")
        response.side_effect = [
            {
                'ids':
                [
                    'uuid_01',
                    'uuid_02',
                    'uuid_03',
                ]
            }
        ]
        with mock_simple_salesforce(response):
            adapter = self.get_adapter()
            result = adapter.get_updated('2015-12-31 00:00:00')
        self.assertIsInstance(result, types.GeneratorType)
        self.assertEqual(list(result), ['uuid_01', 'uuid_02', 'uuid_03'])

    def test_get_deleted_no_date(self):
        """Test the get_deleted function of the adapter"""
        response = MagicMock(name="get_deleted")
        response.side_effect = [[]]
        with mock_simple_salesforce(response):
            adapter = self.get_adapter()
            result = adapter.get_deleted()
        self.assertIsInstance(result, types.GeneratorType)
        self.assertEqual(list(result), [])

    def test_get_deleted_date(self):
        """Test the get_deleted function of the adapter"""
        response = MagicMock(name="get_deleted")
        response.side_effect = [
            {'deletedRecords': [
                {'deletedDate': u'2015-01-16T11:07:27.000+0000',
                 'id': u'001g000000P7UBDAA3'}],
             'earliestDateAvailable': u'2014-06-23T10:16:00.000+0000',
             'latestDateCovered': u'2015-01-16T11:06:00.000+0000'}
        ]
        with mock_simple_salesforce(response):
            adapter = self.get_adapter()
            result = adapter.get_deleted('2015-01-17 00:00:00')
        self.assertIsInstance(result, types.GeneratorType)
        self.assertEqual(list(result), ['001g000000P7UBDAA3'])

    def test_query(self):
        """Test the query function of the adapter"""
        data = [
            {'records': [
                {'Id': '001g000000P7UBDAA1'},
                {'Id': '001g000000P7UBDAA2'}]}
        ]
        response = MagicMock(name="query")
        response.side_effect = data
        soql = 'Select id from %s where id in %s'
        with mock_simple_salesforce(response):
            adapter = self.get_adapter()
            result = adapter.query(soql,
                                   'Account',
                                   ('001g000000P7UBDAA1',
                                    '001g000000P7UBDAA2'))
            self.assertEqual(result, data[0])

    def test_create(self):
        """Test the create function of the adapter"""
        response = MagicMock(name="create")
        response.side_effect = [
            {'errors': [], 'id': '001g000000P7UBDAA1'}
        ]
        with mock_simple_salesforce(response):
            adapter = self.get_adapter()
            result = adapter.create(
                {'Name': 'A name'}
            )
        self.assertEqual(result, '001g000000P7UBDAA1')

    def test_create_error(self):
        """Test the create function of the adapter raise correct error"""
        response = MagicMock(name="create")
        response.side_effect = [
            {'errors': ['Woups'], 'id': False}
        ]
        with mock_simple_salesforce(response):
            adapter = self.get_adapter()
            with self.assertRaises(SalesforceRESTAPIError):
                adapter.create({})

    def test_write(self):
        """Test the create function of the adapter"""
        response = MagicMock(name="write")
        response.side_effect = [
            200,
        ]
        with mock_simple_salesforce(response):
            adapter = self.get_adapter()
            result = adapter.write(
                '001g000000P7UBDAA1',
                {'Name': 'A new name'}
            )
        self.assertEqual(result, 200)

    def test_exists(self):
        """Test the exists function of the adapter"""
        response = MagicMock(name="exists")
        response.side_effect = [
            {'records': [
                {'Id': '001g000000P7UBDAA1'}]}
        ]
        with mock_simple_salesforce(response):
            adapter = self.get_adapter()
            result = adapter.exists('001g000000P7UBDAA1')
        self.assertEqual(result, True)

    def test_upsert(self):
        """Test the upsert function of the adapter"""
        response = MagicMock(name="upsert")
        response.side_effect = [
            {'records': [
                {'Id': '001g000000P7UBDAA1'}]},
            '001g000000P7UBDAA1',
            {'errors': [], 'id': '001g000000P7UBDA45'}
        ]
        with mock_simple_salesforce(response):
            adapter = self.get_adapter()
            result = adapter.upsert(
                '001g000000P7UBDAA1',
                {'Name': 'A new name'}
            )
            self.assertEqual(result, '001g000000P7UBDAA1')
            result = adapter.upsert(
                None,
                {'Name': 'An other new name'}
            )
            self.assertEqual(result, '001g000000P7UBDA45')

    def test_error_management(self):
        """Test that the error_handler context manager behave as expected"""
        with self.assertRaises(SalesforceSecurityError):
            with error_handler(MagicMock()):
                raise SalesforceAuthenticationFailed('dummy code',
                                                     'Login failed')
        with self.assertRaises(SalesforceSessionExpiredError):
            with error_handler(MagicMock()):
                raise SalesforceExpiredSession('url', 'status',
                                               'resource_name', 'content')
        with self.assertRaises(SalesforceResponseError):
            with error_handler(MagicMock()):
                raise SalesforceGeneralError('url', 'status',
                                               'resource_name', 'content')
