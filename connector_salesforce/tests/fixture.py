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
"""Salesforce API fixture data"""
contact = {
    'Id': 'uuid_contact_01',
    'MailingStreet': 'Contact street',
    'MailingPostalCode': 'Contact zip',
    'MailingCity': 'Contact city',
    'MailingState': 'Contact state',
    'MailingCountryCode': 'CH',
    'Fax': '+41 21 619 10 10',
    'Phone': '+41 21 619 10 12',
    'Title': 'Contact function',
    'OtherPhone': '+41 21 619 10 13',
    'MobilePhone': '+41 21 619 10 14',
    'AssistantPhone': '+41 21 619 10 15',
    'Email': 'contact@mail.ch',
    'AccountId': 'uuid_account_01',
    'LastName': 'Contact lastname',
    'FirstName': 'Contact firstname',
}

account = {
    'Id': 'uuid_account_01',
    'Name': 'Main name',
    'BillingStreet': 'Main street',
    'BillingPostalCode': 'Main zip',
    'BillingCity': 'Main city',
    'BillingState': 'Main state',
    'BillingCountryCode': 'CH',
    'Fax': '+41 21 619 10 10',
    'Phone': '+41 21 619 10 12',
    'VATNumber__c': 'Main vat',
    'ShippingStreet': 'Shipping street',
    'ShippingPostalCode': 'Shipping zip',
    'ShippingCity': 'Shipping city',
    'ShippingState': 'Shipping state',
    'ShippingCountryCode': 'CH',
    'CurrencyIsoCode': 'EUR',
}

price_book_entry = {
    'Id': 'uuid_pricebookentry_01',
    'UnitPrice': 200.0,
    'CurrencyIsoCode': 'EUR',
    'Product2Id': 'uuid_product_01',
}

opportunity = {
    'Id': 'uuid_opportunity_01',
    'AccountId': 'uuid_account_01',
    'CurrencyIsoCode': 'EUR',
    'Name': 'A won opportunity',

}

opportunity_line = {
    'Id': 'uuid_opportunityline_01',
    'Discount': 20,
    'Description': 'A sale',
    'ListPrice': 100.0,
    'Quantity': 2.0,
    'OpportunityId': 'uuid_opportunity_01',
}
