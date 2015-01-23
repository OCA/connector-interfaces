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
from .unit.exporter_synchronizer import export_record, deactivate_record


def delay_export(session, model_name, record_id):
    """ Delay a job which export a binding record.
    :param session: current session
    :type session: :py:class:`openerp.addons.connector.
                              session.ConnectorSession`

    :param model_name: name of the binding model.
                       In our case `connector.salesforce.xxx`
    :type model_name: str

    :record_id: The id of the binding model record
    :type record_id: int or long
    """
    record = session.browse(model_name, record_id)
    export_record.delay(
        session,
        model_name,
        record.backend_id.id,
        record.id
    )


def delay_deactivate(session, model_name, record_id):
    """ Delay a job which deactivate a binding record.

    :param session: current session
    :type session: :py:class:`openerp.addons.connector.
                              session.ConnectorSession`

    :param model_name: name of the binding model.
                       In our case `connector.salesforce.xxx`
    :type model_name: str

    :record_id: The id of the binding model record
    :type record_id: int or long
    """
    record = session.browse(model_name, record_id)
    deactivate_record.delay(
        session,
        model_name,
        record.backend_id.id,
        record.id
    )
