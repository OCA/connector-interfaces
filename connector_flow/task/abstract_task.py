# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 initOS GmbH & Co. KG (<http://www.initos.com>).
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

from openerp.addons.connector.session import ConnectorSession
from openerp import _
import simplejson
from base64 import b64encode, b64decode


class AbstractTask(object):

    def __init__(self, cr, uid, ids):
        self.session = ConnectorSession(cr, uid)
        assert len(ids) == 1, "Single instance id expected"
        self._id = ids[0]

    def run_task(self, task_id, **kwargs):
        return self.session.env['impexp.task'].browse(task_id).do_run(**kwargs)

    def related_action(self, job=None, **kwargs):
        """Overwrite this method to add a related action function
           for a specific task type."""
        pass

    def run(self, **kwargs):
        """All the task core action happens here"""
        raise Exception("Not Implemented")

    def run_successor_tasks(self, **kwargs):
        successors = self.session.env['impexp.task.transition'].\
            search_read([('task_from_id', '=', self._id)], ['task_to_id'])
        retval = None
        for succ in successors:
            retval = self.run_task(succ['task_to_id'][0], **kwargs)
        return retval

    def create_file(self, filename, data):
        ir_attachment = self.session.env['ir.attachment'].\
            create({'name': filename,
                    'datas': b64encode(data),
                    'datas_fname': filename})
        impexp_file = self.session.env['impexp.file'].\
            create({'attachment_id': ir_attachment.id,
                    'task_id': self._id,
                    'state': 'done'})
        return impexp_file.id

    def load_file(self, file_id):
        f = self.session.env['impexp.file'].browse(file_id)
        if f.attachment_id.datas:
            return b64decode(f.attachment_id.datas)
        return None


def action_open_chunk(chunk_id):
    """Window action to open a view of a given chunk"""
    return {
        'name': _("Chunk"),
        'type': 'ir.actions.act_window',
        'res_model': 'impexp.chunk',
        'view_type': 'form',
        'view_mode': 'form',
        'res_id': chunk_id,
    }


class AbstractChunkReadTask(AbstractTask):
    """Task that reads (and processes) an existing chunk of data"""

    def run(self, chunk_id=None, **kwargs):
        chunk = self.session.env['impexp.chunk'].browse(chunk_id)
        chunk_data = chunk.data
        kwargs['chunk_data'] = simplejson.loads(chunk_data)
        new_state = 'failed'
        result = None
        try:
            result = self.read_chunk(**kwargs)
            new_state = 'done'
        except:
            raise
        finally:
            chunk.write({'state': new_state})
        return result

    def read_chunk(self, **kwargs):
        pass

    def related_action(self, job=None, **kwargs):
        """Returns window action to open the chunk belonging to the job.
           This is an example for a related action function."""
        chunk_id = job.kwargs.get('chunk_id')
        if chunk_id:
            return action_open_chunk(chunk_id)


class AbstractChunkWriteTask(AbstractTask):
    """Task that writes (and feeds) data as a chunk"""
    def write_and_run_chunk(self, chunk_data, chunk_name,
                            async=True, **kwargs):
        chunk = self.session.env['impexp.chunk'].\
            create({'name': chunk_name,
                    'data': simplejson.dumps(chunk_data)})
        return self.run_successor_tasks(chunk_id=chunk.id,
                                        async=async,
                                        **kwargs)
