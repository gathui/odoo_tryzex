# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError, UserError

class CompanyInherit(models.Model):
    _inherit = 'res.company'
    
    case_file_prefixcode = fields.Char(string='Case File Prefix', size=4, help=" 2-4 letter Prefix code to be attached to your case files")
    procurement_email = fields.Char(string="Procurement Email")
    recruitment_email = fields.Char(string="Recruitment Email")
    