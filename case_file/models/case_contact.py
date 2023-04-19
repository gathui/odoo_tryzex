from odoo import models, fields, api
import requests
from datetime import date, datetime

import logging
_logger = logging.getLogger(__name__)

class CaseFileContact(models.Model):
    _name = 'case.contact'
    _description = 'Case Contact'
    _check_company_auto = True

    name=fields.Char(string="Name", default=lambda obj: obj.env['ir.sequence'].next_by_code('case.file.contact'))
    contact_name = fields.Char(string="Contact Name")
    case_file_id = fields.Many2one('case.file', string="Case File", check_company=True)
    company_id = fields.Many2one('res.company', string="Company",default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string="Partner ID", check_company=True, help="Related Record of contact stored in our database")
    phone_number = fields.Char(string='Phone')
    email = fields.Char(string='Phone')
    active = fields.Boolean(string="Active", default=True)
    contact_type = fields.Selection([
        ('police', 'Police'),
        ('court_clerk', 'Court Clerk'),
        ('magistrate', 'Magistrate'),
        ('witness', 'Witness')
    ], string='Contact Type', help="Type of Contact", )
    description = fields.Char(string="Description")