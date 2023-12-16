from odoo import models, fields, api
import requests
from datetime import date, datetime

import logging
_logger = logging.getLogger(__name__)

class CaseDocumentType(models.Model):
    _name = 'case.document.type'
    _description = 'Case Document Types'
    _check_company_auto = True


    name = fields.Char(string="Document Type")
    category_id = fields.Many2one('case.file.category', string="Case File Category", check_company=True, domain="[('company_id', '=', company_id)]")
    subcategory_id = fields.Many2one('case.file.subcategory', string="Case File Subcategory", check_company=True, domain="[('company_id', '=', company_id)]")
    apply_to_all = fields.Boolean(string="Apply to All Sub-Categories", default=False, help="If checked, this document type will be applied for all sub categories in this Category")
    company_id = fields.Many2one('res.company', string="Company",default=lambda self: self.env.company)  
    required = fields.Boolean(string="Required", default=False, help="Document Required to be attached for this Case Subcategory Type")
    sequence = fields.Integer(string="Document Sequence",help="Sequcen to order the documents", default = 1)
    active = fields.Boolean(string="Active", default=True)


    @api.onchange('apply_to_all')
    def _onchange_apply_to_all(self):
        for rec in self:
            if self.apply_to_all == True:
                rec.subcategory_id = None
                rec.sequence = 0

class CaseDocument(models.Model):
    _name = 'case.document'
    _description = 'Case Documents'
    # _inherit = ['mail.thread','mail.activity.mixin','ir.attachment']
    _check_company_auto = True

    ref=fields.Char(string="Name", default=lambda obj: obj.env['ir.sequence'].next_by_code('case.document'))
    name = fields.Char(string="Document Name")
    case_file_id = fields.Many2one('case.file', string="Case File", check_company=True, domain="[('company_id', '=', company_id)]")
    claimant_id = fields.Many2one(string="Claimant", related="case_file_id.claimant_id")
    document_type_id = fields.Many2one('case.document.type', string="Document Type", check_company=True, domain="[('company_id', '=', company_id)]")
    document_type = fields.Char(string="Document Type", related="document_type_id.name")
    category_id = fields.Many2one(string="Category", related="case_file_id.category_id")
    subcategory_id = fields.Many2one(string="Sub Category", related="case_file_id.subcategory_id")
    document_sequence = fields.Integer(string="Sequence", related="document_type_id.sequence")
    company_id = fields.Many2one('res.company', string="Company",default=lambda self: self.env.company)
    
    attachment_id = fields.Many2one('ir.attachment', string="Attachment")    
    active = fields.Boolean(string="Active", default=True)
    description = fields.Char(string="Description")

    def name_get(self):
        result = []   
        for rec in self:
            result.append((rec.id, '[%s] - %s' % (str(rec.document_sequence),str(rec.name))))                
                
        return result