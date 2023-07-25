from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta



class HRExpenseInherit(models.Model):
    _inherit = "hr.expense"
    _check_company_auto = True


    partner_id = fields.Many2one('res.partner', string="Related Partner", check_company=True, domain="[('company_id', '=', company_id)]", 
                                 help="Related Record of contact stored in our database")
    case_file_id = fields.Many2one('case.file', string="Related Case File", check_company=True, domain="[('company_id', '=', company_id)]")
    

    
    @api.depends('partner_id')
    @api.onchange('partner_id')
    def _onchange_partner_name(self):
        for rec in self:        
            if rec.partner_id != rec.case_file_id.claimant_id :
                rec.case_file_id.claimant_id = None