from odoo import models, fields, api
import requests
from datetime import date, datetime

import logging
_logger = logging.getLogger(__name__)

class CaseAct(models.Model):
    _name = 'case.act'
    _description = 'Laws of Kenya'

    ref=fields.Char(string="Reference", default=lambda obj: obj.env['ir.sequence'].next_by_code('case.act'))
    name = fields.Char(string="Act Number")
    act_title = fields.Char(string="Act Title")
    url = fields.Char(string="URL")
    description = fields.Char(string="Description")
    
    active = fields.Boolean(string="Active", default=True)

    def name_get(self):
        result = []   
        for rec in self:
            result.append((rec.id, '%s - %s' % (str(rec.name),str(rec.act_title))))                
                
        return result