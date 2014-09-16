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
from lxml import etree

from openerp import models, fields, api

from openerp.addons.connector import session as csession, connector
from openerp.addons.connector.connector import install_in_connector
from .unit.import_synchronizer import (batch_import,
                                       delayed_batch_import,
                                       ODBCSynchronizer)
install_in_connector()


class import_configurator(models.TransientModel):
    """ODBC import register
    Each created register will correspond to
    a model to import using ODBC
    """
    _name = 'connector.odbc.import.configurator'

    _rec_name = 'model_id'

    model_id = fields.Many2one(
        'ir.model',
        'What to import'
    )
    backend_id = fields.Many2one(
        'connector.odbc.data.server.backend',
        'Backend to configure',
        required=True,
        default=lambda self: self._get_default_backend(),
    )
    priority = fields.Integer(
        'Priority',
        help='Smaller value = greater priority'
    )

    @api.model
    def _get_default_backend(self):
        """Retrieve active id from context"""
        active_id = self.env.context.get('active_id')
        if not active_id:
            active_ids = self.env.context.get('active_ids', [None])
            active_id = active_ids[0]
        assert active_id, "No active_id in context"
        return self.env['connector.odbc.data.server.backend'].browse(active_id)

    @api.model
    def _get_valid_importers(self, backend_id):
        """Return a list of valid model name

        Model must be bound to a :py:class:``.unit.importer.ODBCSynchronizer``
        subclass

        :backend_id: id of a `` model

        :return: list of corresponding class
        :rtype: list
        """

        def _classes(backend_class, accumulator):
            """Recursively get all the registered class for a given
            backend

            :param backend_class: Connector backend class to introspect
            :type backend_class: :py:class:`connector.backend.Backend`
            :param accumulator: accumulation list for the result
            :type accumulator: list

            :return: a set of available class registered to the unit
                     note a registered class is a named tuple
                     with cls, openerp_module, replaced_by keys
            :rtype: list
            """
            assert isinstance(accumulator, list)
            accumulator.extend(backend_class._class_entries)
            if not backend_class.parent:
                return accumulator
            return _classes(backend_class.parent, accumulator)

        backend_model = self.env['connector.odbc.data.server.backend']
        irmodel_model = self.env['ir.model']
        backend = backend_model.browse(backend_id)
        backend_class = backend.get_backend()[0]
        avail_models = [x.cls._model_name for x in _classes(backend_class, [])
                        if issubclass(x.cls, ODBCSynchronizer)]
        model_ids = irmodel_model.search([('model', 'in', avail_models)])
        if not model_ids:
            raise NotImplementedError(
                'No class overriding ODBCSynchronizer are available'
            )
        return model_ids

    @api.multi
    def create_register(self):
        """Create a import register from model fields value

        This will add a model to import with odbc backend
        """
        register_model = self.env["connector.odbc.import.register"]
        for current in self:
            data = {
                'backend_id': current.backend_id.id,
                'model_id': current.model_id.id,
                'sequence': current.priority,
            }
            register_model.create(data)
        return True

    def fields_view_get(self, cr, uid, view_id=None, view_type=False,
                        context=None, toolbar=False, submenu=False):
        """Add dynamic domain on model_id field

        In order to popose a domain Odoo model linked to
        `ODBCSynchronizer` subclasses using the connector
        backend class decorator
        """
        if context is None:
            context = self.pool['res.users'].context_get(cr, uid)
        backend_id = self._get_default_backend(cr, uid, context=context)
        res = super(import_configurator, self).fields_view_get(
            cr,
            uid,
            view_id=view_id,
            view_type=view_type,
            context=context,
            toolbar=toolbar,
            submenu=submenu
        )
        doc = etree.XML(res['arch'])
        nodes = doc.xpath("//field[@name='model_id']")
        model_ids = self._get_valid_importers(cr, uid, backend_id.id,
                                              context=context)
        for node in nodes:
            node.set(
                'domain',
                "[('id', 'in', [%s])]" % ', '.join([str(x.id) for x in model_ids])
            )
        res['arch'] = etree.tostring(doc)
        return res


class odcb_register(models.Model):
    """Configurable connector model register"""

    _name = "connector.odbc.import.register"

    _order = 'sequence'
    _rec_name = 'model_id'

    model_id = fields.Many2one(
        'ir.model',
        'What to Import',
        readonly=True,
        required=True
    )

    sequence = fields.Integer(
        'Priority',
        required=True
    )

    last_import_date = fields.Datetime(
        'Last import date'
    )
    backend_id = fields.Many2one(
        'connector.odbc.data.server.backend',
        'Related Backend',
        required=True
    )

    @api.multi
    def direct_import(self):
        for register in self:
            register.backend_id.direct_import([register.model_id.model])
        return True

    @api.multi
    def delay_import(self):
        for register in self:
            register.backend_id.delay_import([register.model_id.model])
        return True


class odbc_backend(models.Model):
    """Base ODBC Data sync backend with odbc supported server"""

    _name = "connector.odbc.data.server.backend"
    _inherit = "connector.backend"
    _description = """Base ODBC Data sync with ODBC supported backend"""
    _backend_type = "odbc_server"

    @api.multi
    def get_environment(self, model_name, filter=None):
        session = csession.ConnectorSession(
            self.env.cr,
            self.env.uid,
            self.env.context
        )
        backend = self
        env = connector.Environment(backend, session, model_name)
        return env

    def _select_versions(self):
        """ Available versions

        Can be inherited to add custom versions.
        """
        return [('1.0', '1.0')]

    dsn = fields.Char('DSN', required=True)
    version = fields.Selection(
        _select_versions,
        string='Version',
        required=True
    )
    import_register_ids = fields.One2many(
        'connector.odbc.import.register',
        'backend_id',
        'Model to import'
    )

    @api.one
    @api.returns('connector.odbc.import.register')
    def _get_register(self, model_name, context=None):
        current = self
        try:
            return next(x for x in current.import_register_ids
                        if x.model_id.model == model_name)
        except StopIteration:
            raise ValueError('No register for model %s' % model_name)

    @api.multi
    def _import(self, models, mode, full=False,):
        assert mode in ['direct', 'delay'], "Invalid mode"
        session = csession.ConnectorSession(
            self.env.cr,
            self.env.uid,
            self.env.context
        )
        import_start_time = fields.Datetime.now()
        for backend in self:
            for model in models:
                register = backend._get_register(model)
                date = register.last_import_date if not full else False
                if mode == 'direct':
                    batch_import(session, model, backend['id'],
                                 date=date)
                else:
                    delayed_batch_import(session, model, backend['id'],
                                         date=date)
            register.write(
                {'last_import_date': import_start_time},
            )
        return True

    @api.multi
    def delay_import(self, models, full=False):
        return self._import(models, 'delay', full=full)

    @api.multi
    def direct_import(self, models, full=False):
        return self._import(models, 'direct', full=full)

    @api.one
    def import_all(self):
        """Do a global direct import of all data"""
        models = self.import_register_ids
        models = [x.model_id.model for x in models]
        return self.direct_import(models, full=False)

    @api.one
    def import_all_delayed(self):
        """Do a global delayed import of all data"""
        models = self.import_register_ids
        models = [x.model_id.model for x in models]
        return self.delay_import(models, full=False)


class base_odbc_binding(models.AbstractModel):

    _name = "obdc.base.server.binding"
    _inherit = 'external.binding'

    backend_id = fields.Many2one(
        'connector.odbc.data.server.backend',
        'ODBC Data Backend',
        required=True,
        ondelete='restrict'
    )


class odbc_binding(models.AbstractModel):
    """Abstact class to create binding between backend browse odbc id, openerp id
    based on a string code"""

    _inherit = 'obdc.base.server.binding'
    _name = "odbc.string.server.binding"
    _description = """Abstact binding class for ODBC data"""

    odbc_code = fields.Char(
        'ODBC unique Code',
        help="Store unique value of ODBC source"
        " mulitpe key is not supported yet"
    )


class odbc_numerical_binding(models.AbstractModel):
    """Abstact class to create binding between backend browse odbc id, openerp id
    based on a numerical id"""

    _name = "odbc.numerical.server.binding"
    _inherit = 'obdc.base.server.binding'
    _description = """Abstact binding class for odbc data"""
    odbc_code = fields.Integer(
        'ODBC numerical unique id',
        help="Store unique value of ODBC source"
        " mulitpe key is not supported yet"
    )


class odbc_datetime_binding(models.AbstractModel):
    """Abstact class to create binding between backend browse odbc id, openerp id
    based on a datetime"""

    _name = "odbc.datetime.server.binding"
    _inherit = 'obdc.base.server.binding'
    _description = """Abstact binding class for odbc data"""

    odbc_code = fields.Datetime(
        'ODBC datetime unique id',
        help="Store unique value of ODBC source"
        " mulitpe key is not supported yet"
    )
