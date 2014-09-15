# -*- coding: utf-8 -*-
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
from __future__ import absolute_import
from datetime import datetime
from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

from openerp.addons.connector import session as csession, connector
from openerp.addons.connector.connector import install_in_connector
from .unit.import_synchronizer import (batch_import,
                                       delayed_batch_import,
                                       ODBCSynchronizer)
install_in_connector()

# TODO transform this into model related to backend.
# This should be manually configurable
MODEL_REGISTRY = []


class import_configurator(orm.TransientModel):
    _name = 'connector.odbc.import.configurator'

    _rec_name = 'model_id'

    _columns = {
        'model_id': fields.many2one(
            'ir.model',
            'What to import'
        ),
        'backend_id': fields.many2one(
            'connector.odbc.data.server.backend',
            'Backend to configure',
            required=True
        ),
        'priority': fields.integer(
            'Priority',
            help='Smaller value = greater priority'
        ),
    }

    def _get_default_backend(self, cr, uid, context=None):
        if context is None:
            context = self.pool['res.users'].context_get(cr, uid)
        active_id = context.get('active_id')
        if not active_id:
            active_ids = context.get('active_ids', [None])
            active_id = active_ids[0]
        assert active_id, "No active_id in context"
        return active_id

    _defaults = {'backend_id': _get_default_backend}

    def _get_valid_importer(self, cr, uid, backend_id, context=None):
        """Return the name of valid bining model

        That are bound to a ``ODBCSynchronizer`` subclass

        """
        backend_model = self.pool['connector.odbc.data.server.backend']
        model_model = self.pool['ir.model']
        backend = backend_model.browse(cr, uid, backend_id, context=context)
        avail_models = set(x._model_name for x in backend._class_entries
                           if issubclass(x, ODBCSynchronizer))
        model_ids = self.search(cr, uid, ['model', 'in', avail_models])
        if not model_ids:
            raise NotImplementedError(
                'No class overriding ODBCSynchronizer are available'
            )
            return [x.id for x in
                    model_model.browse(cr, uid, model_ids, context=context)]

    def create_register(self, cr, uid, ids, context=None):
        register_model = self.pool["connector.odbc.data.import.register"]
        if isinstance(ids, (int, long)):
            ids = [ids]
        assert len(ids) == 1
        for current in self.browse(cr, uid, ids, context=context):
            data = {
                'backend_id': current.backend_id.id,
                'model_id': current.model_id.id,
                'sequence': current.priority,
            }
            register_model.create(cr, uid, data, context=context)
        return True


class odcb_register(orm.Model):
    """Configurable connector model register"""

    _name = "connector.odbc.data.import.register"

    _order = 'sequence'
    _rec_name = 'model_id'

    _columns = {
        'model_id': fields.many2one(
            'ir.model',
            'What to Import',
            readonly=True,
            required=True
        ),

        'sequence': fields.integer(
            'Priority',
            required=True
        ),
        'backend_id': fields.many2one(
            'connector.odbc.data.server.backend',
            'Related Backend',
            required=True
        )
    }


class odbc_backend(orm.Model):
    """Base ODBC Data sync backend with odbc supported server"""

    _name = "connector.odbc.data.server.backend"
    _inherit = "connector.backend"
    _description = """Base ODBC Data sync with ODBC supported backend"""
    _backend_type = "odbc_server"

    def get_environment(self, cursor, uid, ids, model_name,
                        filter=None, context=None):
        if context is None:
            context = {}
        if isinstance(ids, list):
            assert len(ids) == 1, "You can get environement only for one id"
            back_id = ids[0]
        else:
            back_id = ids
        session = csession.ConnectorSession(cursor, uid, context=context)
        backend = session.browse(self._name, back_id)[0]
        env = connector.Environment(backend, session, model_name)
        return env

    def _select_versions(self, cr, uid, context=None):
        """ Available versions

        Can be inherited to add custom versions.
        """
        return [('1.0', '1.0')]

    _columns = {
        'dsn': fields.char('DSN', required=True),
        'last_import_start_date': fields.datetime(
            'Last import start date'
        ),
        'version': fields.selection(
            _select_versions,
            string='Version',
            required=True
        ),
        'import_register_ids': fields.one2many(
            'connector.odbc.data.import.register',
            'backend_id',
            'Model to import')
    }

    def _import(self, cursor, uid, ids, models, mode,
                full=False, context=None):
        assert mode in ['direct', 'delay'], "Invalid mode"
        context = context or {}
        session = csession.ConnectorSession(cursor, uid, context=context)
        if isinstance(ids, (int, long)):
            ids = [ids]
        df = DEFAULT_SERVER_DATETIME_FORMAT
        import_start_time = datetime.now().strftime(df)

        for backend in self.read(cursor, uid, ids, context=context):
            for model in models:  # to be done in UI when time available.
                date = backend['last_import_start_date'] if not full else False
                if mode == 'direct':
                    batch_import(session, model, backend['id'],
                                 date=date)
                else:
                    delayed_batch_import(session, model, backend['id'],
                                         date=date)
            self.write(
                cursor, uid,
                backend['id'],
                {'last_import_start_date': import_start_time},
                context=context
            )
        return True

    def delay_import(self, cursor, uid, ids, models, full=False, context=None):
        return self._import(cursor, uid, ids, models, 'delay',
                            full=full, context=context)

    def direct_import(self, cursor, uid, ids, models,
                      full=False, context=None):
        return self._import(cursor, uid, ids, models, 'direct',
                            full=full, context=context)

    def import_all(self, cursor, uid, ids, context=None):
        """Do a global direct import of all data"""
        models = MODEL_REGISTRY
        return self.direct_import(cursor, uid, ids, models,
                                  full=True, context=context)

    def synchronize_all(self, cursor, uid, ids, context=None):
        """Do a global direct import of all data"""
        models = MODEL_REGISTRY
        return self.delay_import(cursor, uid, ids, models,
                                 full=True, context=context)


class base_odbc_binding(orm.AbstractModel):

    _name = "obdc.base.server.binding"
    _inherit = 'external.binding'

    _columns = {
        'backend_id': fields.many2one('connector.odbc.data.server.backend',
                                      'ODBC Data Backend',
                                      required=True,
                                      ondelete='restrict'),
    }


class odbc_binding(orm.AbstractModel):
    """Abstact class to create binding between backend browse odbc id, openerp id
    based on a string code"""

    _inherit = 'obdc.base.server.binding'
    _name = "odbc.string.server.binding"
    _description = """Abstact binding class for ODBC data"""

    _columns = {
        'odbc_code': fields.char('ODBC unique Code',
                                 help="Store unique value of ODBC source"
                                 " mulitpe key is not supported yet"),
    }


class odbc_numerical_binding(orm.AbstractModel):
    """Abstact class to create binding between backend browse odbc id, openerp id
    based on a numerical id"""

    _name = "odbc.numerical.server.binding"
    _inherit = 'obdc.base.server.binding'
    _description = """Abstact binding class for odbc data"""
    _columns = {
        'odbc_code': fields.integer('ODBC numerical unique id',
                                    help="Store unique value of ODBC source"
                                    " mulitpe key is not supported yet"),
    }


class odbc_datetime_binding(orm.AbstractModel):
    """Abstact class to create binding between backend browse odbc id, openerp id
    based on a datetime"""

    _name = "odbc.datetime.server.binding"
    _inherit = 'obdc.base.server.binding'
    _description = """Abstact binding class for odbc data"""
    _columns = {
        'odbc_code': fields.datetime('ODBC datetime unique id',
                                     help="Store unique value of ODBC source"
                                     " mulitpe key is not supported yet")
    }
