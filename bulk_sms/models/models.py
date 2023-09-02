# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
import requests
from datetime import date, datetime,timedelta
import json

import logging
_logger = logging.getLogger(__name__)

class BulkSms(models.Model):
    _name = 'bulk.sms'
    _description = 'Bulk SMS Module'
    _order = "processed_time desc"
    _check_company_auto = True

    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    bulk_sms_setting_id = fields.Many2one('bulk.sms.settings',  string='Bulk SMS Setting', help="Default Bulk SMS Provider",
                                          default=lambda self: self.company_id.bulk_sms_setting_id)
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
    other_details = fields.Char(string="Other Details")
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
    

    @api.model
    def create(self, vals):
        if vals.get("bulk_sms_setting_id",False) == False:
            company_id = self.env['res.company'].search([('id','=',vals["company_id"])])
            if company_id and company_id.bulk_sms_setting_id:
                vals["bulk_sms_setting_id"] = company_id.bulk_sms_setting_id.id
            
        return super().create(vals)
    
    
    def _bulk_sms_cron(self):
        _logger.warning('Starting SMS Cron at: ' + str(datetime.now()))

        #do not send SMS in Test Instance
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

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
                    if rec.scheduled_send_date < datetime.now()+ timedelta(hours=24):
                        rec.write({
                            'status_code': '999',
                            'processed':True,
                            'processed_time': datetime.now(),
                            'status_code_description': "ARCHIVED",
                            'max_retries' : 5
                        })
                    else:
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


    def bulk_sms_cron_tolcin(self):
        company_id = self.env.company
        if company_id and company_id.bulk_sms_setting_id:
            self._bulk_sms_cron_tolcin(company_id.id, company_id.bulk_sms_setting_id.id)


    def _bulk_sms_cron_tolcin(self, company_id, bulk_sms_setting_id):
        _logger.warning(_('Starting Tolcin Bulk SMS Cron >> self._bulk_sms_cron_tolcin(%s, %s) at: %s ')%(company_id,bulk_sms_setting_id,str(datetime.now())))

        #do not send SMS in Test Instance
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if base_url not in ['http://odoo.nguyo-kariuki.com:8069', 'https://odoo.nguyo-kariuki.com:8069'] or\
            'localhost' in base_url:
            _logger.warning('Sending Messages has been disabled in Test Instance ' + str(base_url))
            # return

        #fetch settings    
        setting_id = self.env['bulk.sms.settings'].search([('id','=',bulk_sms_setting_id),('company_id','=',company_id)])
        print('SMSsetting_id',setting_id)
        if setting_id:
            sms_batch_size = 50

            if not sms_batch_size:
                sms_batch_size = 50

            # Process SMS in batches
            result= self.env['bulk.sms'].sudo().search(
                [
                    ('bulk_sms_setting_id','=', setting_id.id),
                    ('processed', '=', False), ('phone_number', '!=', False),
                    ('scheduled_send_date', '<=', datetime.now()), ('active','=',True),
                    ('max_retries','<',5)
                ],
                order="scheduled_send_date",limit=sms_batch_size)
            print('SMSsetting_idresult',result)

            json_str = json.loads(setting_id.sms_status_codes)
            sms_status_codes = json_str or "{}"

            for rec in result:
                try:
                    archive_date = (datetime.now() - timedelta(hours=24))
                    print("RECHERE",rec, archive_date)
                    if rec.scheduled_send_date < archive_date:
                        rec.write({
                            'status_code': '999',
                            'processed':True,
                            'processed_time': datetime.now(),
                            'status_code_description': "ARCHIVED",
                            'max_retries' : 5
                        })
                    else:
                        headers = {'Content-Type': 'application/x-www-form-urlencoded', 
                        'Accept': 'application/json'}
                        json_str = json.loads(setting_id.sms_api_settings)
                        json_str ["msisdn"] = rec.phone_number
                        json_str["message"] = rec.text_message
                        print("JSONSTR", json_str)
                        my_response = requests.post(url=setting_id.sms_api_base_url, data=json.dumps(json_str), headers=headers)
                        sent_sms_response=my_response.json() or []
                        _logger.warning(_('SMS sent_sms_response:\n\tRequest:%s\n\tResponse:%s')%(my_response,sent_sms_response))

# [{"StatusCode":1,"MessageId":"TOL_fa37c15bde14e27811121fc76cbcddfbbc18c3de","Description":"Sent","Message":"Hello World
# - Testing","Message_parts":1,"Recipient":"254723068523","Telco":"safaricom","Credits":1}]

#                         [{"StatusCode":1,"MessageId":"TOL_54ddfc785ea339e3d36bc8c0c398e27daf1396e6","Description":"Sent","Message":"Hello World
# -
# Testing","Message_parts":1,"Recipient":"254723068523","Telco":"safaricom","Credits":1},{"StatusCode":1,"MessageId":"TOL_d0234d6c6104efb2ee9c5be7ebaf0b289f3a0074","Description":"Sent","Message":"Hello
# World - Testing","Message_parts":1,"Recipient":"254703469511","Telco":"safaricom","Credits":1}]

                        if sent_sms_response and len(sent_sms_response)>0 and\
                            "MessageId" in sent_sms_response[0].keys():
                            sms_api_response = sent_sms_response[0]
                            message_id = sms_api_response['MessageId']
                            sms_cost = sms_api_response['Credits']
                            status_code = sms_api_response['StatusCode']
                            status_code_description = sms_api_response['Description']
                            status_other_details = [{"Telco":str(sms_api_response['Telco']).upper}]

                            for sms_code in sms_status_codes:
                                if sms_code == status_code:
                                    status_code_description = sms_status_codes[sms_code]

                            rec.write({
                                'processed': True,
                                'message_id': message_id,
                                'status_code': status_code,
                                'cost': sms_cost,
                                'processed_time': datetime.now(),
                                'status_code_description': status_code_description,
                                'other_details': status_other_details
                            })
                        elif sent_sms_response and len(sent_sms_response)>0 and\
                            "MessageId" not in sent_sms_response[0].keys():
                            sms_api_response = sent_sms_response[0]
                            message_id = "000XXX"
                            sms_cost = sms_api_response['Credits']
                            status_code = sms_api_response['StatusCode']
                            status_code_description = sms_api_response['Description']

                            for sms_code in sms_status_codes:
                                if sms_code == status_code:
                                    status_code_description = sms_status_codes[sms_code]

                            rec.write({
                                'processed': True,
                                'message_id': message_id,
                                'status_code': status_code,
                                'cost': sms_cost,
                                'processed_time': datetime.now(),
                                'status_code_description': status_code_description,                                
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