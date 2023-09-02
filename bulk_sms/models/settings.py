from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import json
import logging
_logger = logging.getLogger(__name__)


def validateJSON(jsonData):
    try:
        m = json.loads(jsonData)
    except Exception as e:
        _logger.warning(_("Error converting JSON text (Bulk SMS Settings)\n\tJSON Data Received:\n%s\n\tError:%s")%(jsonData,e))
        return False
    return True

class BulkSMSSettings(models.Model):
    _name = 'bulk.sms.settings'
    _description = 'Bulk SMS Settings'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    name =fields.Char(string="Name", default=lambda obj: obj.env['ir.sequence'].next_by_code('bulk.sms.setting'))
    bulk_sms_provider = fields.Char(string="Bulk SMS Provider", help="Bulk SMS Provider eg Infobip, Twilio, Africas Talking")
    
    sms_api_base_url = fields.Char(string="SMS API URL", help="URL to which POST endpoint is called")
    sms_api_settings = fields.Text(string="SMS API Settings (JSON)", help="Provide JSON settings for the API connection",default="{}")
    sms_status_codes = fields.Text(string="SMS Status Code (JSON)", help="SMS Status Codes as returned from the Bulk SMS API",default="{}")
    active = fields.Boolean(string="Active", default = False)

    africastalking_username=fields.Char(string="Africas Talking User Name")
    africastalking_base_url= fields.Char(string="Africas Talking Base URL")
    africastalking_apiKey= fields.Char(string="Africas Talking API Key")
    africastalking_sms_header=fields.Char(string="Africas Talking SMS Header")
    sms_batch_size = fields.Integer(string="SMS Batch Size", help="No of SMS to Process Per Batch", default=50)
   

    
    @api.onchange('sms_api_settings','sms_status_codes')
    def _onchange_sms_api_settings(self):
        for rec in self:
            if validateJSON(rec.sms_api_settings) == False and rec.active == True:
                rec.active = False
                raise UserError("Cannot save record, the JSON String is invalid")
            

    def name_get(self):
        result = []   
        for rec in self:
            result.append((rec.id, '%s - %s' % (str(rec.name),str(rec.bulk_sms_provider))))                
                
        return result
