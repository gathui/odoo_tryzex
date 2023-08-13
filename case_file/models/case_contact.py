from odoo import models, fields, api
import requests
from datetime import date, datetime

import logging
_logger = logging.getLogger(__name__)

class CaseFileContact(models.Model):
    _name = 'case.contact'
    _description = 'Case Contact'
    _inherit = ['mail.thread','mail.activity.mixin']
    _check_company_auto = True

    ref=fields.Char(string="Name", default=lambda obj: obj.env['ir.sequence'].next_by_code('case.contact'))
    name = fields.Char(string="Contact Name")
    case_file_id = fields.Many2one('case.file', string="Case File", check_company=True, domain="[('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', string="Company",default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string="Related Partner", check_company=True, domain="[('company_id', '=', company_id)]", 
                                 help="Related Record of contact stored in our database")
    phone_number = fields.Char(string='Phone')
    alt_phone_number = fields.Char(string='Alternate Phone')
    email = fields.Char(string='Email')
    address = fields.Char(string='address')
    active = fields.Boolean(string="Active", default=True)
    contact_type = fields.Selection([
        ('respondent','Respondent'),
        ('opposing_counsel','Opposing Counsel'),
        ('police', 'Police'),
        ('court_clerk', 'Court Clerk'),
        ('magistrate', 'Magistrate'),
        ('judge', 'Judge'),
        ('witness', 'Witness'),
        ('victim', 'Victim'),
        ('other', 'Other'),

    ], string='Contact Type', help="Type of Contact", )
    description = fields.Char(string="Description")

    # def name_get(self):
    #     result = []   
    #     for rec in self:
    #         result.append((rec.id, '%s - %s' % (str(rec.name),str(rec.contact_name))))                
                
    #         return result