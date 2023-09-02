# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError, UserError

class CompanyInherit(models.Model):
    _inherit = 'res.company'
    
    bulk_sms_setting_id = fields.Many2one('bulk.sms.settings',  string='Bulk SMS Setting', help="Default Bulk SMS Provider")
    

    @api.onchange('bulk_sms_setting_id')
    def onchange_bulk_sms_setting_id(self):
        for rec  in self:
            if rec.bulk_sms_setting_id.active == False:
                raise UserError("Cannot set an in-active Bulk SMS Provider Setting")
            # elif rec.bulk_sms_setting_id.active and rec.bulk_sms_setting_id.validateJSON(rec.bulk_sms_setting_id.sms_api_settings) == False:
            #     raise UserError("The Bulk SMS Settings JSON are invalid")