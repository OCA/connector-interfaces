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
from openerp.tools.translate import _
import simplejson
from base64 import b64encode, b64decode


class abstract_task(object):

    def __init__(self, cr, uid, ids):
        self.session = ConnectorSession(cr, uid)
        self._id = ids[0]

    def run_task(self, task_id, **kwargs):
        return self.session.pool.get('impexp.task') \
            .do_run(self.session.cr, self.session.uid, [task_id], **kwargs)

    def related_action(self, job=None, **kwargs):
        """Overwrite this method to add a related action function
           for a specific task type."""
        pass

    def run(self, **kwargs):
        """All the task core action happens here"""
        raise Exception("Not Implemented")

    def run_successor_tasks(self, **kwargs):
        transition_ids = self.session.search('impexp.task.transition',
                                             [('task_from_id', '=',
                                               self._id)])
        successor_ids = self.session.read('impexp.task.transition',
                                          transition_ids,
                                          ['task_to_id'])
        retval = None
        for trans in successor_ids:
            retval = self.run_task(trans['task_to_id'][0], **kwargs)
        return retval

    def create_file(self, filename, data):
        ir_attachment_id = self.session.create(
            'ir.attachment',
            {'name': filename,
             'datas': b64encode(data),
             'datas_fname': filename})
        file_id = self.session.create(
            'impexp.file',
            {'attachment_id': ir_attachment_id,
             'task_id': self._id,
             'state': 'done'})
        return file_id

    def load_file(self, file_id):
        f = self.session.browse('impexp.file', file_id)
        if not f.attachment_id.datas:
            return None
        return b64decode(f.attachment_id.datas)


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


class abstract_chunk_read_task(abstract_task):
    """Task that reads (and processes) an existing chunk of data"""

    def run(self, chunk_id=None, **kwargs):
        chunk = self.session.read('impexp.chunk',
                                  chunk_id,
                                  ['data'])['data']
        kwargs['chunk_data'] = simplejson.loads(chunk)
        new_state = 'failed'
        result = None
        try:
            result = self.read_chunk(**kwargs)
            new_state = 'done'
        except:
            raise
        finally:
            self.session.write('impexp.chunk', chunk_id, {'state': new_state})
        return result

    def read_chunk(self, **kwargs):
        pass

    def related_action(self, job=None, **kwargs):
        """Returns window action to open the chunk belonging to the job.
           This is an example for a related action function."""
        chunk_id = job.kwargs.get('chunk_id')
        if chunk_id:
            return action_open_chunk(chunk_id)


class abstract_chunk_write_task(abstract_task):
    """Task that writes (and feeds) data as a chunk"""
    def write_and_run_chunk(self, chunk_data, chunk_name,
                            async=True, **kwargs):
        chunk_id = self.session.create('impexp.chunk',
                                       {'name': chunk_name,
                                        'data': simplejson.dumps(chunk_data)})
        return self.run_successor_tasks(chunk_id=chunk_id,
                                        async=async,
                                        **kwargs)
