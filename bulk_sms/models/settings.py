from email.policy import default
from odoo import api, fields, models, _


class BulkSMSSettings(models.Model):
    _name = 'bulk.sms.settings'
    _description = 'Bulk SMS Settings'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    name =fields.Char(string="Name", default=lambda obj: obj.env['ir.sequence'].next_by_code('bulk.sms.setting'))
    

    africastalking_username=fields.Char(string="Africas Talking User Name")
    africastalking_base_url= fields.Char(string="Africas Talking Base URL")
    africastalking_apiKey= fields.Char(string="Africas Talking API Key")
    africastalking_sms_header=fields.Char(string="Africas Talking SMS Header")
    sms_batch_size = fields.Integer(string="SMS Batch Size", help="No of SMS to Process Per Batch", default=50)

    
