from odoo import models, fields, api,_
import requests
from datetime import date, datetime

import logging
_logger = logging.getLogger(__name__)

class CaseFileCategory(models.Model):
    _name = 'case.file.category'
    _description = 'Case File Category'
    _order = "name asc"
    _check_company_auto = True

    name=fields.Char(string="Name", default=lambda obj: obj.env['ir.sequence'].next_by_code('case.file.category'))
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    code = fields.Char(string='Code', help="Short Code that will be appended to Case Files eg EMP for Employment cases will create a Case File ID EMP/2000/01/01")
    active = fields.Boolean(string="Active", default=True)

class CaseFileSubCategory(models.Model):
    _name = 'case.file.subcategory'
    _description = 'Case File Sub Category'
    _order = "name asc"
    _check_company_auto = True

    name=fields.Char(string="Name", default=lambda obj: obj.env['ir.sequence'].next_by_code('case.file.subcategory'))
    category_id = fields.Many2one('case.file.category', string="Category")
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    active = fields.Boolean(string="Active", default=True)
    

class CaseFile(models.Model):
    _name = 'case.file'
    _description = 'Case File'
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = "name asc"
    _check_company_auto = True

    name=fields.Char(string="Name", default=lambda obj: obj.env['ir.sequence'].next_by_code('case.file'))

    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    claimant_id = fields.Many2one('res.partner', string = "Claimant", check_company=True)
    respondent_ids = fields.Many2many('res.partner', 'case_respondent_rels',string = "Respondent(s)", check_company=True)
    reference = fields.Char('Reference')
    case_number = fields.Char('Case Number')
    tracking_number = fields.Char('Tracking Number')
    citation_reference = fields.Char('Citation')
    case_commentary = fields.Char('Commentary', help="Top level commmentary about the case. For more detailed information, enter in the Details under the details tab")
    details = fields.Text('Details')
    category_id = fields.Many2one('case.file.category', string="Category", check_company=True)
    subcategory_id = fields.Many2one('case.file.subcategory', string="Sub Category", check_company=True)
    state = fields.Selection([
        ('Open', 'Open'),
        ('Closed', 'Closed'),
        ('Canceled', 'Canceled')
    ], string='Status', default='Open', help="Status of the expense.", group_expand='_expand_states',)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    case_contact_ids = fields.One2many('case.contact','case_file_id', string="Case Contact", check_company=True)



    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]
    

    @api.model
    def create(self,vals):
        print('VALSTOSAVE', vals)
        if vals.get('name', ('New')) == ('New'):
            company_prefix = self.env.company.case_file_prefixcode or 'AA'
            category_id = self.env['case.file.category'].search([('id','=',vals['category_id'])])
            category_code = category_id.code if category_id else 'ZZZ'
            next_sequence = self.env['ir.sequence'].next_by_code('case.file') or ('New')
            new_name = (_('%s/%s/%s')%(company_prefix,category_code,next_sequence))
            vals['name'] = new_name
            
        res = super(CaseFile,self).create(vals)
        return res