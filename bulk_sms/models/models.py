# -*- coding: utf-8 -*-
from odoo import models, fields, api
import requests
from datetime import date, datetime

import logging
_logger = logging.getLogger(__name__)

class BulkSms(models.Model):
    _name = 'bulk.sms'
    _description = 'Bulk SMS'
    _order = "processed_time desc"
    _check_company_auto = True

    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    name=fields.Char(string="Name", default=lambda obj: obj.env['ir.sequence'].next_by_code('bulk.sms'))
    phone_number=fields.Char(string='Phone Number', required=True)
    text_message=fields.Char(string='Text Message(SMS)')
    retry_duration=fields.Integer(string='SMS Retry Duration In Hours')
    processed=fields.Boolean(string='Processed',default=False)
    scheduled_send_date= fields.Datetime(string='Scheduled Send Date')
    processed_time= fields.Datetime(string='Processed Time')
    message_id= fields.Char(string='Message Id')
    status_code = fields.Integer(string='Status Code')
    cost=fields.Char(string='Cost')
    status_code_description = fields.Char(string='Status Code Description')
    company_id = fields.Many2one('res.company', string="Company")
    related_record = fields.Reference (
        selection = [
            ('case.file', 'Case File'), 
            ('res.partner', 'Client'), 
            ('res.users', 'User'),
            ('hr.employee', 'Employee'),
            ('account.move','Customer Invoice'),
            ('crm.lead','Opportunity'),
            ('mpesa.base','MPesa')
        ],
        string = "Related Record"
    )
    active = fields.Boolean(string="Active", default=True)
    sms_tag = fields.Char(string = "Tag")
    max_retries = fields.Integer(string="Retry Attempts", default =0)
    
    def _bulk_sms_cron(self):
        _logger.warning('Starting SMS Cron at: ' + str(datetime.now()))

        #do not send SMS in Test Instance
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if base_url not in ['http://odoo.saner.gy', 'https://odoo.saner.gy','https://saner-gy-sanergy.odoo.com','http://saner-gy-sanergy.odoo.com']:
            _logger.warning('Sending Messages has been disabled in Test Instance ' + str(base_url))
            return

        #fetch settings
        setting_id = self.env['bulk.sms.setting'].search([('company_id','=',self.company_id.id)])
        if setting_id:
            africastalking_username = setting_id.africastalking_username
            africastalking_base_url= setting_id.africastalking_base_url
            africastalking_apiKey= setting_id.africastalking_apiKey
            africastalking_sms_header=setting_id.africastalking_sms_header
            _sms_batch_size = setting_id.sms_batch_size
            sms_batch_size = 50

            try:
                int(_sms_batch_size)
                sms_batch_size = int(_sms_batch_size)
            except:
                sms_batch_size = 50

            if not sms_batch_size:
                sms_batch_size = 50

            # Process SMS in batches
            result= self.env['bulk.sms'].sudo().search(
                [
                    ('processed', '=', False), ('phone_number', '!=', False),
                    ('scheduled_send_date', '<=', datetime.now()), ('active','=',True),
                    ('max_retries','<',5)
                ],
                order="scheduled_send_date",limit=sms_batch_size)

            sms_status_codes = {
                100: "Processed",
                101: "Sent",
                102: "Queued",
                401: "RiskHold",
                402: "InvalidSenderId",
                403: "InvalidPhoneNumber",
                404: "UnsupportedNumberType",
                405: "InsufficientBalance",
                406: "UserInBlacklist",
                407: "CouldNotRoute",
                500: "InternalServerError",
                501: "GatewayError",
                502: "RejectedByGateway"
            }

            _logger.warning('AT Headers \n' +str(africastalking_base_url)+'\n' + str(result))
            for rec in result:
                try:

                    headers = {'Content-Type': 'application/x-www-form-urlencoded', 
                    'Accept': 'application/json',
                    'apiKey': africastalking_apiKey} 
                    body= {
                        'username': africastalking_username,
                        'from': africastalking_sms_header,
                        'to': rec.phone_number,
                        'message': rec.text_message
                    }

                    my_response = requests.post(url=africastalking_base_url, data=body, headers=headers)
                    sent_sms_response=my_response.json()
                    _logger.warning('SMS sent_sms_response' +str (sent_sms_response))
                    if sent_sms_response:
                        africastalking_response = sent_sms_response['SMSMessageData']['Recipients'][0]
                        message_id = africastalking_response['messageId']
                        sms_cost = africastalking_response['cost']
                        status_code = africastalking_response['statusCode']
                        status_code_description = "Unknown Status Code"

                        for sms_code in sms_status_codes:
                            if sms_code == status_code:
                                status_code_description = sms_status_codes[sms_code]

                        rec.write({
                            'processed': True,
                            'message_id': message_id,
                            'status_code': status_code,
                            'cost': sms_cost,
                            'processed_time': datetime.now(),
                            'status_code_description': status_code_description
                        })
                    else:
                        if rec.max_retries + 1 >= 5:
                            status_msg = 'Maximum retries reached'
                            _processed = True
                        else:
                            status_msg = 'Could not send SMS'
                            _processed = False
                            
                        rec.write({
                            'status_code': '999',
                            'processed':_processed,
                            'processed_time': datetime.now(),
                            'status_code_description': status_msg,
                            'max_retries' : rec.max_retries + 1
                        })
                except Exception as e:
                    _logger.warning (f'sorry, we have a problem: {e}')
                    
                    if rec.max_retries + 1 >= 5:
                        status_msg = 'Maximum retries reached'
                        _processed = True
                    else:
                        status_msg = str(e)
                        _processed = False
                    rec.write({
                        'status_code': '999',
                        'processed':_processed,
                        'processed_time': datetime.now(),
                        'status_code_description': status_msg,
                        'max_retries' : rec.max_retries + 1
                    })
        else:
            _logger.warning ('Could not send SMS: No Settings Available')