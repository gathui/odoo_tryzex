# -*- coding: utf-8 -*-
from odoo import _, http
from odoo.http import request
# from odoo.http import request, JsonRequest, Response
import json
import requests
from requests.auth import HTTPBasicAuth
import logging
from datetime import datetime, date, timedelta
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)

# def alternative_json_response(self, result=None, error=None):
#     if error is not None:
#         response = error

#     if result is not None:
#         response = result

#     mime = 'application/json'
#     body = json.dumps(response, default=date_utils.json_default)
#     return Response(
#         body, status=error and error.pop('http_status', 200) or 200,
#         headers=[('Content-Type', mime), ('Content-Length', len(body))]
#     )

class BulkSms(http.Controller):
   
    @http.route('/bulk_sms/getsms', type='json', auth='public', website=True)
    def getSms(self, request):
        processed=request.params['processed']
        result= request.env['bulk.sms'].sudo().search([('processed', '!=', processed)])
        x = datetime.datetime.now()
        data = []
        for rec in result:
            schedule = datetime.datetime.combine(rec.scheduled_send_date, datetime.time(0, 0))
            if schedule <= x: 
                vals=   {
                            'message': rec.text_message,
                            'phoneNumber': rec.phone_number,
                            'statusCode': rec.status_code,
                            'cost': rec.cost,
                            'processed': rec.processed,
                            'scheduledSendDate': rec.scheduled_send_date
                        }
                data.append(vals)
        
        json_data ={'status':200, 'response': data, 'message': 'success'}
        return json_data

    @http.route('/bulk_sms/send_sms', type='json', auth='public', methods=['POST'])
    def send_sms(self, **kw):
        try:
            sms_detail = request.jsonrequest or {}
            
            if sms_detail:  
                sms = {
                    "phone_number": sms_detail['phone_number'],
                    "text_message": sms_detail['sms_msg'],
                    "retry_duration": 1,
                    "scheduled_send_date": datetime.now()+ timedelta(minutes=15),
                    'company_id':sms_detail['company_id'],
                    'related_record':sms_detail['related_record'],
                    'sms_tag':sms_detail['sms_tag'],
                    'active':True
                }
                resp = request.env['bulk.sms'].sudo().create(sms)

                # request._json_response = alternative_json_response.__get__(request, JsonRequest)

                return({
                    'sms_id': resp.id,
                    'status':'Success',
                    'message':''})
        except Exception as e:
            _logger.warning('Error creating SMS: \n'  + str(e))
            # request._json_response = alternative_json_response.__get__(request, JsonRequest)
            return({
                    'sms_id': 0,
                    'status':'Error',
                    'message':str(e)})
        

    @http.route('/bulk_sms/get_sms_status/<int:sms_id>', methods=['GET'], type='http', auth='public')
    def get_sms_status(self, sms_id, **kw):
        resp = {
                    'sms_id':0,
                    'status_code': None,
                    'status_code_description': None,
                    'processed': False,
                    'processed_time':None,
                    'cost' : 0
                }
                
        if sms_id:
            try:
                # _sms_id = int(float(sms_id))
                sms = request.env['bulk.sms'].search([('id','=',_sms_id)])
                # if sms:
                #     # request._json_response = alternative_json_response.__get__(request, JsonRequest)
                #     return ({
                #         'sms_id':sms.id,
                #         'status_code': sms.status_code,
                #         'status_code_description': sms.status_code_description,
                #         'processed':sms.processed,
                #         'processed_time':sms.processed_time,
                #         'cost' : sms.cost
                #     })
                # else:
                #     return resp
            except Exception as e:
                _sms_id = 0         
                return resp               
        else:
            return resp
