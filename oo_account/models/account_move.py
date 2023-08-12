# -*- coding: utf-8 -*-


import base64
from odoo import fields, models, _
import os
class AccountMove(models.Model):
    _inherit = 'account.move'
    
    def _get_template(self):
        
        file = "journal_entries_import_template.csv"
        template_path = os.path.join(os.path.join(os.path.dirname(__file__), file))
        self.journal_template = base64.b64encode(open(template_path, "rb").read())

    journal_template = fields.Binary('Template', compute="_get_template")

    
    def get_import_templates(self):
        return {
            'type': 'ir.actions.act_url',
            'name':  _('Import Template for Journal Entries'),
            'url': '/web/content/account.move/%s/journal_template/journal_entries_import_template.csv?download=true' %(self.id),
        }
