# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010-2015 Elico Corp (<http://www.elico-corp.com>)
#    Authors: Liu Lixia
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

from openerp.addons.connector.unit.synchronizer import Deleter
from openerp.tools.translate import _
from openerp.addons.connector_dns.connector import get_environment
from openerp.addons.connector.queue.job import job


class DNSDeleter(Deleter):
    """ Base deleter for Dnspod """

    def run(self, binding_id, data):
        """ Run the synchronization, delete the record on Dnspod

        :param magento_id: identifier of the record to delete
        """
        self.backend_adapter.delete(data)
        return _('Record %s deleted on Dnspod') % binding_id


@job
def export_delete_record(session, model_name, backend_id, binding_id, data):
    """ Delete a record on Dnspod """
    env = get_environment(session, model_name, backend_id)
    exporter = env.get_connector_unit(DNSDeleter)
    return exporter.run(binding_id, data)
