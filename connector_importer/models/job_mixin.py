# Author: Simone Orsi
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, exceptions, fields, models

from odoo.addons.queue_job.job import DONE


class JobRelatedMixin(models.AbstractModel):
    """Mixin klass for queue.job relationship."""

    _name = "job.related.mixin"
    _description = __doc__

    job_id = fields.Many2one("queue.job", string="Job", readonly=True)
    job_state = fields.Selection(index=True, related="job_id.state")

    def has_job(self):
        return bool(self.job_id)

    def job_done(self):
        return self.job_state == DONE

    def _check_delete(self):
        if self.has_job() and not self.job_done():
            raise exceptions.Warning(_("You must complete the job first!"))

    def unlink(self):
        for item in self:
            item._check_delete()
        return super().unlink()
