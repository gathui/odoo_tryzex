from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
import re
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import string    
import random 



class ResPartnerInherit(models.Model):
    _inherit = "res.partner"
    _check_company_auto = True

    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    physical_address = fields.Char(string="Last Name")
    gender = fields.Selection([
        ('Male', 'Male'),
        ('Female', 'Female'),
    ], string='Gender', store=True, default='')
    date_of_birth = fields.Date(string="Date of Birth")
    age =fields.Integer (string="Age", compute="_compute_age")
    
    @api.model
    def _get_default_country(self):
        country = self.env['res.country'].search([('code', '=', 'KE')], limit=1)

        return country
    nationality = fields.Many2one('res.country', string="Nationality", default=_get_default_country)
    id_type = fields.Selection([
        ('national_id', 'National ID'),
        ('passport_id', 'Passport ID'),
        ('other', 'Other ID'),
    ], string='identification Type', store=True, default='national_id')
    national_id = fields.Char(string="National ID")
    passport_id = fields.Char(string="Passport ID")
    
    next_of_kin_ids = fields.Many2many('res.partner', 'next_of_kin_rel', 'case_file_partner_id', 'next_of_kin_partner_id', string="Next of Kin", check_company=True)


    @api.model
    def create(self,vals):
        vals["ref"] = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 8))
        vals["company_id"] = self.env.company.id
        res = super(ResPartnerInherit,self).create(vals)
        return res
    

    @api.onchange('first_name','last_name')
    def _onchange_partner_name(self):
        for rec in self:
            _first_name = str(rec.first_name).strip().title() if rec.first_name else ""
            _last_name = str(rec.last_name).strip().title() if rec.last_name else ""
            if str(_last_name + _first_name ).strip() != '':
                rec.first_name = _first_name
                rec.last_name = _last_name
                rec.name =(_("%s %s") % (_first_name, _last_name))


    @api.depends('date_of_birth')
    def _compute_age(self):
        for record in self:
            if record.date_of_birth and record.date_of_birth <= fields.Date.today():
                record.age = relativedelta(
                    fields.Date.from_string(fields.Date.today()),
                    fields.Date.from_string(record.date_of_birth)).years 
            else: 
                record.age = 0
    
    