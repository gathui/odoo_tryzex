# -*- coding: utf-8 -*-

import re
from odoo import _, http
from odoo.http import request, JsonRequest, Response
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

class MpesaController947100(http.Controller):
    @http.route('/lipa_online/c2b_validation_url/947100', type='json', auth='public', methods=['POST'])
    def c2b_validation_url(self, **kw):
        # MPesa Response Codes - as at 2022-04-25
        #	ResultCode	ResultDesc
        #	C2B00011	Invalid MSISDN
        #	C2B00012	Invalid Account Number
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