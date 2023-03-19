# -*- coding: utf-8 -*-

import re
from odoo import _, http
from odoo.http import request, Response
from marine_utils.models.http import JsonRequest
import json
import requests
from requests.auth import HTTPBasicAuth
import logging
from datetime import datetime, date, timedelta
import base64
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)


def alternative_json_response(self, result=None, error=None):
    if error is not None:
        response = error

    if result is not None:
        response = result

    mime = 'application/json'
    body = json.dumps(response, default=date_utils.json_default)
    return Response(
        body, status=error and error.pop('http_status', 200) or 200,
        headers=[('Content-Type', mime), ('Content-Length', len(body))]
    )

def check_if_sandbox_env_safe(self):
    #check if we are in sandbox environment
    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    if base_url not in ['http://odoo.saner.gy', 'https://odoo.saner.gy','https://saner-gy-sanergy.odoo.com','http://saner-gy-sanergy.odoo.com']:
        #check MPESA URLs
        mpesa_recs = request.env['settings'].sudo().search([])
        for rec in mpesa_recs:
            if str(rec.mpesa_express_url).find('sandbox.safaricom.co.ke') < 1 or\
                str(rec.stk_confirmation_url).find('odoo.saner.gy') > 0 or\
                str(rec.stk_push_url).find('odoo.saner.gy') > 0 or\
                str(rec.stk_push_url).find('odoo.saner.gy') > 0 :

                _logger.warning('Action not allowed in Test Instance: ' + str(base_url) + '\n' + rec.name)
                return False
        return True

class MpesaBase(http.Controller):
    @http.route('/lipa_online/c2b_validation_url/', type='json', auth='public', methods=['POST'])
    def c2b_validation_url(self, **kw):
        # MPesa Response Codes - as at 2022-04-25
        #	ResultCode	ResultDesc
        #	C2B00011	Invalid MSISDN
        #	C2B00012	Invalid Account nNumber
        #	C2B00013	Invalid Amount
        #	C2B00014	Invalid KYC Details
        #	C2B00015	Invalid Shortcode
        #	C2B00016	Other Error
        try:
            vals = request.jsonrequest or {}
            _logger.warning('MPesa Validation Params: ' + str(vals))
            
            _bill_ref_number = vals['BillRefNumber']
            _bill_ref_number = ''.join(_bill_ref_number.split())
            _bill_ref_number = _bill_ref_number.upper()

            respval =  {
                "ResultCode": 0,
                "ResultDesc": "Accepted"
            }
            
            request._json_response = alternative_json_response.__get__(request, JsonRequest)

            return respval 
        except Exception as e:
            _logger.warning('Error performing MPesa Validation: \n'  + str(e))


    # MPESA C2B
    @http.route('/lipa_online/c2b_confirmation_url/<int:paybill_number>', type='json', auth='public', methods=['POST'], csrf=False)
    def c2b_confirmation_url(self, paybill_number, **kw):
        headers = {'Content-Type': 'application/json'}
        print('Called MPesa', paybill_number)
        if check_if_sandbox_env_safe  == False:
            return
        mpesa_settings = request.env['mpesa.settings'].sudo().search([('paybill_number','=',paybill_number),
        ('active','=',True)], limit=1)
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        try:
            mpesa_payment = request.jsonrequest or {}
            print('MPesa Confirm Params: ', mpesa_payment)
            
            _bill_ref_number = mpesa_payment['BillRefNumber']
            _bill_ref_number = ''.join(_bill_ref_number.split())
            _bill_ref_number = _bill_ref_number.upper()

            transaction_data_received = {
                "paybill_number":paybill_number,
                "transaction_id": mpesa_payment['TransID'],
                "payer_name": mpesa_payment['FirstName'],
                "description": mpesa_payment['TransID'],
                "payer_phone_number": mpesa_payment['MSISDN'],
                "amount": mpesa_payment['TransAmount'],
                "reference": _bill_ref_number,
                "organization_balance": mpesa_payment['OrgAccountBalance'],
                "type": mpesa_payment['TransactionType'],
                "trans_time": mpesa_payment['TransTime'],
                "company_id": mpesa_settings.company_id.id or None
            }

            if transaction_data_received:
                pay = request.env['mpesa.base'].sudo().create_c2b_payment(transaction_data_received)
                print('Created C2B Payment ' , str(pay))
                return Response(json.dumps({"data": {"payment_id":str(pay)},"status":"Success", "message": "Success"}), headers=headers)
            else:
                _logger.warning('Error creating MPesa Transaction: No transaction_data_received')
                return Response(json.dumps({"data": {}, "status":"Error", "message": "Error creating MPesa Transaction: No transaction_data_received"}), headers=headers)
        except Exception as e:
            _logger.warning('Error creating MPesa Transaction: \n'  + str(e))
            return Response(json.dumps({"data": {},"status":"Error", "message": str(e)}), headers=headers)
        
        # {
        # "TransactionType":"Pay Bill",
        # "TransID":"RKTQDM7W6S",
        # "TransTime":"20191122063845",
        # "TransAmount":"10",
        # "BusinessShortCode":"600638",
        # "BillRefNumber":"A123",
        # "InvoiceNumber":"",
        # "OrgAccountBalance":"49197.00",
        # "ThirdPartyTransID":"",
        # "MSISDN":"2547*****149",
        # "FirstName":"John",
        # }


    #STK/Lipa Na Mpesa Express Confirmation URL
    @http.route('/lipa_online/stk_confirmation_url/<int:paybill_number>', auth='public', type='json')
    def stk_confirmation_url(self, paybill_number, **args):
        _logger.warning('Confirmation URL Initiated >>>')
        if check_if_sandbox_env_safe  == False:
            return

        try:
            params = request.jsonrequest or {}
            _logger.warning('Confirmation URL Called >>>'+ str(params))
            if params:
                data = params['Body']['stkCallback']
                res_code = data.get('ResultCode')
                if res_code == 0:  # success mpesa code
                    vals = {"payload": params}
                    pay = request.env['mpesa.stk'].sudo().update_checkout(data)
                    _logger.warning('Checkout Updated Successfully')
                elif res_code > 0:
                    pay = request.env['mpesa.stk'].sudo().update_checkout_error(data)
                    _logger.warning("UPDATED CHECKOUT BUT WITH_ERROR" + str(pay))
                else:
                    _logger.warning('Could not create mpesa transaction >>>'+ str(params))
                
            else:
                _logger.warning('could not call confirmation URL')
            return "Completed"
        except Exception as e:
            _logger.warning('CONFIRMATION URL ERROR >>> \n' + str(e))
            return "Completed"
        finally:
            return "Completed"


    @http.route('/lipa_online/send_stk_push/<int:paybill_number>', methods=['POST'], auth='public', type='json')
    def send_stk_push(self, paybill_number, **kw):
        stk_response = json.loads(request.httprequest.data)
        _logger.warning('STK Called >>> \n' + str(stk_response))
        
        if check_if_sandbox_env_safe== False:
            return
        print('LOG paybill_number >>>',paybill_number)
        try:
            if stk_response:
                _paybill_number = paybill_number
                _phone_number = stk_response.get('phone_number', False)
                _amount = stk_response.get('amount', False)
                _payment_reference = stk_response.get('ref', False)
                _company_id = 0

                if _paybill_number and _phone_number and _amount and _payment_reference:
                    _logger.warning('MPesa Have payment details: ' + str(_phone_number))
                    MpesaAccessToken = request.env['mpesa.settings'].sudo().search([
                        ('paybill_number','=',_paybill_number),
                        ('active','=',True)], limit=1)
                    
                    if MpesaAccessToken:                       
                        _company_id = MpesaAccessToken.company_id.id

                        r = requests.get(MpesaAccessToken.authorisation_url,
                                        auth=HTTPBasicAuth(MpesaAccessToken.consumer_key,
                                                            MpesaAccessToken.consumer_secret))
                        print('MpesaAccessToken rrr',str(r.text), MpesaAccessToken.authorisation_url,MpesaAccessToken.consumer_key,
                                                            MpesaAccessToken.consumer_secret)

                        mpesa_access_token = json.loads(r.text)
                        print('MpesaAccessToken',mpesa_access_token)
                        lipa_time = datetime.now().strftime('%Y%m%d%H%M%S')
                        validated_mpesa_access_token = mpesa_access_token['access_token']
                        data_to_encode = MpesaAccessToken.paybill_number + MpesaAccessToken.mpesa_express_pass_key + lipa_time
                        online_password = base64.b64encode(data_to_encode.encode())
                        decode_password = online_password.decode('utf-8')
                        access_token = validated_mpesa_access_token
                        api_url = MpesaAccessToken.mpesa_express_url
                        headers = {'Content-Type': 'application/json', "Authorization": "Bearer %s" % access_token}
                        payload = {
                            "BusinessShortCode": MpesaAccessToken.paybill_number,
                            "Password": decode_password,
                            "Timestamp": lipa_time,
                            "TransactionType": "CustomerPayBillOnline",
                            "Amount": int(_amount),
                            "PartyA": int(_phone_number),
                            "PartyB": MpesaAccessToken.paybill_number,
                            "PhoneNumber": int(_phone_number),
                            "CallBackURL": MpesaAccessToken.stk_confirmation_url,
                            "AccountReference": _payment_reference,
                            "TransactionDesc": _payment_reference
                        }
                        _logger.warning('STK PAyload' + str(payload))
                        _response = requests.request("POST", api_url, headers=headers, data=json.dumps(payload)) or {}
                        if _response:
                            stk_response = _response.json()
                            res_code = stk_response['ResponseCode']

                            if res_code == '0':
                                payload['company_id'] = _company_id
                                payload['paybill_number'] = _paybill_number
                                print('LOG paybill_number 2 >>>',paybill_number, _paybill_number, _company_id)
                                pay = request.env['mpesa.stk'].sudo().create_checkout(payload, stk_response)
                                _logger.warning('CREATED CHECKOUT SUCCESS' + str(pay))
                            else:
                                _logger.warning('CALL TO STK FAILED: Result Code: ' + str(res_code))
                        else:
                            _logger.warning('CALL TO STK FAILED >>>' + str(_response))
                    else:
                        _logger.warning('CALL TO STK FAILED >>> No valid MPesa Token Details Found')
                else:
                    _logger.warning('CALL TO STK FAILED >>> Invalid STK Params Provided: ' + 
                    '{Paybill Number: ' + str(_paybill_number) + ', Phone: ' + str(_phone_number) + ', Amount: ' +str(_amount)  + ', Payment Reference: ' + str(_payment_reference) + '}')
            else:
                _logger.warning('Missing JSON values for STK' + str(kw))
        except Exception as e:
            _logger.warning('ERROR AT STK PUSH >>> \n' + str(e) + '\n' + r.text)
        finally:
            # return {"success":"ok"}   
            return "Completed"

    @http.route('/lipa_online/search_pit_emptier_by_id', methods=['GET'],  auth='public')
    def search_pit_emptier_by_id(self, **kw):
        headers = {'Content-Type': 'application/json'}
        company_id = request.params.get('company_id')
        id_number = request.params.get('id_number')
        print('search_pit_emptier_by_id', company_id,id_number)
        if id_number and company_id:
            try:
                res = []
                result = request.env['res.partner'].sudo().search([
                    ('id_number','=',id_number),('company_id','=',int(company_id))])

                if result:
                    for data in result:
                        vals = {
                            'partnerId': data.id,
                            'partnerName':data.name,
                            'id_number':data.id_number,
                        }

                        res.append(vals)

                    return Response(json.dumps({"data": res, "message": "Success"}), headers=headers)
                else:
                    return Response(json.dumps({"data": res, "message": "No Pit Emptier Found"}), headers=headers)
            except Exception as e:
                return Response(json.dumps({"message": e}, default=str), headers=headers)
        else:
            return Response(json.dumps({"data": {}, "message": "No Search Parameters Provided"}), headers=headers)
