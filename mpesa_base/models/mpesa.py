from datetime import date, timedelta, datetime
from urllib import response
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, ValidationError

import requests
import json
import logging
_logger = logging.getLogger(__name__)

def convert_to_float(num):
    try:
        float(num)
        return float(num)
    except ValueError:
        return 0

def convert_to_date(date_val):
    _dt_trans_time =  datetime(2000, 1, 1)
    if date_val and len(str(date_val)) == 14:
        _dt_trans_time = datetime.strptime(str(date_val), '%Y%m%d%H%M%S')
        _dt_trans_time = _dt_trans_time - timedelta(hours=3) #GMT offset
    else:
        _dt_trans_time = datetime(2000, 1, 1)
    return _dt_trans_time
class MPesaBase(models.Model):
    _name = 'mpesa.base'
    _description = 'MPesa Base'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Name', default=lambda obj: obj.env['ir.sequence'].next_by_code('mpesa.base'))
    paybill_number = fields.Char(string='Paybill Number')
    transaction_type = fields.Char(string='Transaction Type')
    trans_id = fields.Char(string='Transaction ID',
                           help="MPesa Receipt Number: This is the unique M-Pesa transaction ID for every payment "
                                "request")
    trans_time = fields.Char(string='Transaction Time')
    transaction_date_time = fields.Datetime(string="Transaction Date")
    trans_amount = fields.Integer(string='Transaction Amount', currency_field='currency_id')
    bill_ref_number = fields.Char(string='Bill Ref Number', help="Account Payment Reference", tracking=True)
    third_party_trans_id = fields.Char(string='Third Party Transaction ID')
    payer_phone_number = fields.Char(string='Phone Number')
    payer_name = fields.Char(string='Payer Name')
    auto_matched = fields.Boolean(string="Auto Matched", default=False)
    amount_applied = fields.Monetary(string='Amount Applied', currency_field='currency_id')
    amount_residual = fields.Monetary(string='Amount Pending', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', 'Currrency', default=lambda self: self.env.ref('base.KES').id,
                                  help="Currency in use")
    last_processed = fields.Datetime(string="Last Processed Date", default=datetime.now())     
    comments = fields.Char(string="Comments")      
    account_payment_id = fields.Many2one('account.payment', string="Account Payment Entry", tracking=True)   
    company_id = fields.Many2one('res.company', string="Company")
    partner_id = fields.Many2one('res.partner', string="Customer")
    stk_id = fields.Many2one('mpesa.stk', string="STK Entry")
    active = fields.Boolean(string="Active", default=True)    

    
    def _compute_transaction_time(self):
        for rec in self:
            if rec.trans_time and len(rec.trans_time) == 14:
                _dt_trans_time = datetime.strptime(rec.trans_time, '%Y%m%d%H%M%S')
                rec.transaction_date_time = _dt_trans_time
            else:
                rec.transaction_date_time = datetime(2000, 1, 1)
                
    
    def search_for_partner(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url=""
        if self.paybill_number == "174379":
            url = base_url + str("/sales_custom/partner?uniqueCode=") + str(self.bill_ref_number).strip() +\
                "&company_id=" + str(self.company_id.id)
        elif self.paybill_number == "947100":
            url = base_url + str("/sales_custom/partner?uniqueCode=") + str(self.bill_ref_number).strip()+\
                "&company_id=" + str(self.company_id.id)
        elif self.paybill_number == "4090387":
            url = base_url + str("/lipa_online/search_pit_emptier_by_id?company_id=2&id_number="+\
                str(self.bill_ref_number).strip())

        r = requests.get(url, auth=None)
                        
        _partner_response = json.loads(r.text)
        _partner_id = 0
        try:            
            if _partner_response and _partner_response["data"][0].get('partnerId'):
                _partner_id = int(float(_partner_response["data"][0].get('partnerId')))
                self.partner_id = _partner_id
                self.create_mpesa_payment_entry(self.paybill_number)
                self.auto_matched = True            
        except Exception as e:
            _logger.warning('Could not fetch the Partner:' + str(e))
        
        #send SMS
        self.send_confirmation_sms(_partner_id)  

        self.last_processed=datetime.now()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


    @api.model
    def create_c2b_payment(self,  vals):
        _logger.warning('MPesa C2B Record Initiated: \n' + str(vals))
        try:
            _mpesa_rec = self.env['mpesa.base'].search(
                        [('trans_id', '=ilike', str(vals.get('transaction_id')).upper())], limit=1)
            if _mpesa_rec:
                print("MPesa Transaction ID '" + str(vals.get('transaction_id')) + "' has been supplied before")
            else:
                # match toilet id
                _bill_ref_number = str(vals.get('reference')).upper()
                _bill_ref_number = ''.join(_bill_ref_number.split())

                # update fields
                _trans_amount = int(convert_to_float(vals.get('amount')))
                _company_id = int(convert_to_float(vals.get('company_id')))
                
                values = {
                    'transaction_type': str(vals.get('transaction_id')),
                    'trans_id': str(vals.get('transaction_id')).upper(),
                    'trans_time': vals.get('trans_time'),
                    'transaction_date_time': convert_to_date(vals.get('trans_time')),
                    'trans_amount': _trans_amount,
                    'amount_applied': 0,
                    'amount_residual': _trans_amount,
                    'bill_ref_number': _bill_ref_number,
                    'payer_phone_number': vals.get('payer_phone_number'),
                    'payer_name': vals.get('payer_name'),
                    'company_id': _company_id, #TODO
                    'paybill_number':vals.get('paybill_number')
                }
                
                rec = self.env['mpesa.base'].sudo().create(values)
                if rec:
                    _logger.warning('MPesa C2B Record Created: ' + str(vals.get('transaction_id')).upper())
                else:
                    _logger.warning('MPesa C2B Record NOT Created: ' +  str(vals.get('transaction_id')).upper())
                return rec
        except Exception as e:
            _logger.warning('Error creating MPesa Transaction: ' + str(vals.get('transaction_id')).upper() + '\n' + str(e))
            return False
            

    def create_mpesa_payment_entry(self, paybill_number):
        _logger.warning('Creating MPesa Entry [' + str(self.trans_id) + ']' )
        #check if an account exists
        if self.partner_id == False:
            _logger.warning('Creating MPesa Entry [' + str(self.trans_id) + '] Failed: No Customer Assigned')
            return False

        #confirm that no other record has similar transaction id
        _count_record = self.env['mpesa.base'].search_count([('trans_id', '=', self.trans_id)])
        
        if _count_record > 1 :
            err_msg = '<pre>The Transaction was not applied and has been nullified: <ul>'\
                '<li>Record Name : ' + str(self.name) + '</li>'\
                '<li>Paybill Number : ' + str(paybill_number) + '</li>'\
                '<li>Transaction ID : ' + str(self.trans_id) + '</li>'\
                '<li>Transaction Amount: ' +  str(self.trans_amount) + '</li>'\
                '<li>Residual Amount: '+  str(self.amount_residual) +'</li>'\
                '<li>Matching Records Found ' + str(_count_record) + '</li></ul></pre>'
            self.message_post(body=err_msg)
            self.update(
                {
                    'name': 'XXXX_' + str(self.trans_id),
                    'trans_id': 'XXXX_' + str(self.trans_id),
                    'trans_amount': 0, #DO THIS TO ENSURE MATCHING DOES NOT HAPPEN
                    'amount_residual': 0, #DO THIS TO ENSURE MATCHING DOES NOT HAPPEN
                    'error': 'XXXX_' + str(self.trans_id),
                    'active':False
                })
            _logger.warning('Creating MPesa Entry [' + str(mpesa_rec.trans_id) + '] Failed: Transaction ID already exists')
            return False
        else:
            # Get Custom Settings
            for rec in self.env['mpesa.settings'].sudo().search([('paybill_number','=',paybill_number),
            ('active','=',True)],limit=1):
                _mpesa_bank_account_id = rec.journal_id.id
                _ar_account_id = rec.ar_account_id.id
                _company_id = rec.company_id.id

            # Register payment
            for mpesa_rec in self:
                _logger.warning('Creating MPesa Entry [' + str(mpesa_rec.trans_id) + '] start payment:' + str(mpesa_rec.account_payment_id))
                if not mpesa_rec.account_payment_id :
                    trans_date = datetime.strptime(mpesa_rec.trans_time, '%Y%m%d%H%M%S').strftime('%Y-%m-%d')
                    #determine ref based on whether FLT or Deposit invoice
                    payment_ref = 'MPESA_UNMATCHED: [' + str(mpesa_rec.trans_id).upper() + ']'
                    
                    #set the right payment ref to ensure invoices with exact same ref are matched
                    if mpesa_rec.partner_id:
                        payment_ref = str(mpesa_rec.partner_id.ref).upper()

                    pmt_vals = {
                        'date': trans_date,
                        'journal_id': _mpesa_bank_account_id,
                        'partner_id': mpesa_rec.partner_id.id,
                        'amount': mpesa_rec.trans_amount,
                        'currency_id': mpesa_rec.currency_id.id,
                        'partner_type': 'customer',
                        'payment_type': 'inbound',
                        'ref': payment_ref.upper(),
                        'mpesa_id':mpesa_rec.id,
                        'destination_account_id': _ar_account_id,
                        'company_id': _company_id,
                        # 'secondary_state':'posted'
                    }
                    print('Payment Record Vals >>> \n' + str(pmt_vals))
                    payment_register = self.env['account.payment'].sudo().create(pmt_vals)

                    #post only if payment created. 
                    if payment_register:
                        payment_register.action_post()
                    
                        #Get Payment Register Record
                        payment_register_id = self.env['account.payment'].sudo().search([('id','=', payment_register.id)])

                        #TODO Reconcile Payment Entries to get FLT Balance
                        self.reconcile_payment_entry(payment_register_id.partner_id.id, payment_register.company_id.id)

                        #Update MPesa Record
                        mpesa_rec.update({
                            'account_payment_id' : payment_register.id,
                            'last_processed':datetime.now(),
                            'amount_applied':mpesa_rec.trans_amount,
                            'amount_residual':0
                        })
                        _logger.warning('Creating MPesa Entry [' + str(mpesa_rec.trans_id) + '] Completed')
                    else:
                        _logger.warning('Creating MPesa Entry [' + str(mpesa_rec.trans_id) + '] Failed: Payment Entry not created')
                else:
                    _logger.warning('Creating MPesa Entry [' + str(mpesa_rec.trans_id) + '] Failed: Already applied')

    def send_confirmation_sms(self, param_partner_id):
        # Create and send the SMS
        _logger.warning('sending SMS:' + str(param_partner_id))
        if param_partner_id or param_partner_id == 0:
            try:
                _partner_id = int(float(param_partner_id))
                partner_id = self.env['res.partner'].search([('id','=', _partner_id)])
                if partner_id:
                    phone_number = partner_id.formatted_phone_no
                    nickname = ' ' + str(partner_id.nickname).strip() if partner_id.nickname else ' Customer'
                    amount_paid = str(self.trans_amount)
                    payment_description = str(self.bill_ref_number)
                    # outstanding_balance = partner_id.total_due
                    related_record = 'res.partner,' + str(partner_id.id)
                    company = partner_id.company_id
                    sms_tag = 'PMTSMSACK-PAYBILL-' + str(self.paybill_number) 
                    sms_to_send = "Thank you" + str(nickname) + ". Your payment of Kshs:" + amount_paid + \
                        " for " + payment_description + " has been received."

                    # if record.related_record:
                    #   outstanding_balance = str(record.related_record.amount_residual)
                    #   related_record = 'account.move,' + str(record.related_record.id)
                        
                    #   sms_to_send += "  Your outstanding balance is Kshs:" + outstanding_balance

                    sms = {
                        "phone_number": "+" + str(self.payer_phone_number),
                        "text_message": sms_to_send,
                        "retry_duration": 1,
                        "scheduled_send_date": datetime.now(),
                        'company_id': company.id,
                        'related_record': related_record,
                        'sms_tag':sms_tag,
                        'active':True
                    }
                    print('SMSACK',sms)
                    self.env['sanergy.bulk.sms'].sudo().create(sms)

                else:
                    print('No valid partner found')
                    sms_to_send = "Thank you. Your payment of Kshs:" + str(self.trans_amount) + \
                        " for " + str(self.bill_ref_number) + " has been received."
                    sms_tag = 'PMTSMSACK-PAYBILL-' + str(self.paybill_number) 
                    sms = {
                        "phone_number": "+" + str(self.payer_phone_number),
                        "text_message": sms_to_send,
                        "retry_duration": 1,
                        "scheduled_send_date": datetime.now(),
                        'company_id': self.company_id.id,
                        'related_record': 'mpesa.base,' + str(self.id),
                        'sms_tag':sms_tag,
                        'active':True
                    }

                    self.env['sanergy.bulk.sms'].sudo().create(sms)
                _logger.warning('SMS Payment Acknowledgement' + str(sms))
            except Exception as e:
                _logger.warning('Could not create the SMS Payment Acknowledgement' + str(e))

    def apply_pending_mpesa_txns(self):
        # Run job to apply any outstanding MPesa amounts to existing invoices
        _logger.warning('Starting MPesa Base Pending Transactions Cron at: ' + str(datetime.now()))
        pending_records = 0
        pending_records = self.env['mpesa.base'].search_count([('account_payment_id', '=', None),
        ('active','=',True),('last_processed','<',datetime.now()+timedelta(minutes=-10))])
        
        if pending_records > 0:
            #Get records not processed in the last 10 minutes
            _mpesa_ids = self.env['mpesa.base'].search([('account_payment_id', '=', None),('active','=',True),
            ('last_processed','<',datetime.now()+timedelta(minutes=-10))],order='last_processed asc',limit=100)
            for rec in _mpesa_ids:
                try:
                    rec.search_for_partner()  
                except Exception as e:
                    _logger.warning('Error processing MPesa Base Cron Job: \n' + str(rec) + ': ' + str(e))

        _logger.warning('MPesa Base Pending Transactions Cron Completed: ' + str(datetime.now()))
 

    # TODO sort this section to recon the payment
    def reconcile_payment_entry(self, partner_id, company_id):
        ''' 
           Called to reconcile invoices and MPesa Payments - if Partner ID = -1 get all partners
        '''
        _logger.warning('Start MPesa Recon for: >>>>>')
        try:

            if partner_id == -1:
                payments = self.env['account.move'].search([
                ('move_type','=','entry'), ('company_id','=', company_id),
                ('payment_id.mpesa_id','!=',False),
                ('state','=','posted')], 
                order='date',limit=500)
            else:
                payments = self.env['account.move'].search([
                    ('partner_id','=',partner_id),
                    ('payment_id.mpesa_id','!=',False),
                    ('move_type','=','entry'), ('company_id','=', company_id),('state','=','posted')], 
                    order='date',limit=500)
            
            _logger.warning('MPesa Recon >>>>>: ' + str(payments))  
            for rec in payments:
                _logger.warning('MPesa Recon Search Payments>>>>>: ' + str(rec) 
                                + '>>>' + str(rec.name)+ ' >>> ' + str(rec.ref))
                invoices = self.env['account.move'].search([('move_type', '=', 'out_invoice'), 
                ('partner_id','=',rec.partner_id.id),
                ('amount_residual', '>', 0), ('ref', '=', rec.ref),
                ('state','=','posted'),('company_id','=',rec.company_id.id)],order="invoice_date_due")

                for inv in invoices:   
                    _logger.warning('MPesa Recon Search INV >>>>>: ' + str(inv))
                    credit_lines = rec.line_ids.filtered(lambda line: line.account_id[0].name == "1200 - Accounts Receivable Control")
                    invoice_lines = inv.line_ids.filtered(lambda line: line.account_id[0].name == "1200 - Accounts Receivable Control")
                    for credit_line in credit_lines:
                        if not credit_line.reconciled and invoice_lines.account_id[0].id == credit_line.account_id[0].id:
                            invoice_lines += credit_line
                            invoice_lines.reconcile()
                            _logger.warning('MPesa Payment Reconciled: ' + str(inv.name))
            _logger.warning('MPesa Payment Reconciliation Finished: ' )
            return True
        except Exception as e:
            _logger.warning('MPesa Payment Reconciliation Failed: ' + str(e))
            return False

    
    @api.constrains('trans_id')
    def _check_trans_id_unique(self):
        for rec in self:
            counts = rec.search_count([('trans_id', '=', rec.trans_id)])

            if counts > 1:
                raise ValidationError("The Transaction ID " + str(rec.trans_id) + " already exists!")

    _sql_constraints = [
        ('_unique_trans_id', 'UNIQUE (trans_id)', 'SQLCONSTERR: MPesa Transaction ID must be unique.')
    ]
    

class MpesaSTK(models.Model):
    """
    model and methods  for handling and storing mpesa
    STK data received through the json CallBackURL
    """
    _name = 'mpesa.stk'
    _description = 'Mpesa STK'
    _order = 'id desc'

    name = fields.Char(string='Name', default=lambda obj: obj.env['ir.sequence'].next_by_code('mpesa.stk'))    
    company_id = fields.Many2one('res.company', string="Company")
    paybill_number = fields.Char(string='Paybill Number')
    payment_reference = fields.Char(string="Payment Reference")
    amount = fields.Monetary('Amount Requested', help="Mpesa Transaction Amount Requested", currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', 'Currrency', default=lambda self: self.env.ref('base.KES').id,
                                  help="Currency in use")
    merchant_request_id = fields.Char('Merchant Request ID')
    checkout_request_id = fields.Char('Checkout Request ID')
    phone_number = fields.Char('Phone Number', help="The customer mpesa phone number")
    mpesa_receipt_number = fields.Char('Mpesa Receipt Number',
                                       help="The reference number as assigned to the transaction by the mobile money provider")
    transaction_date = fields.Char('Transaction Date')
    result_code = fields.Char('Result Code')
    result_desc = fields.Char('Result Description')
    reconciled = fields.Boolean('Reconciled', default=False, help="if checked, then this payment has been reconciled")
    transaction_description = fields.Char(string="Transaction Description")

    
    def convert_to_float(self,num):
        try:
            float(num)
            return float(num)
        except ValueError:
            return 0
    
    def convert_to_date(self,date_val):
        _dt_trans_time =  datetime(2000, 1, 1)
        if date_val and len(str(date_val)) == 14:
            _dt_trans_time = datetime.strptime(str(date_val), '%Y%m%d%H%M%S')
            _dt_trans_time = _dt_trans_time - timedelta(hours=3) #GMT offset
        else:
            _dt_trans_time = datetime(2000, 1, 1)
        return _dt_trans_time

    @api.depends('phone_number', 'mpesa_receipt_number')
    def name_get(self):
        res = []
        for rec in self:
            name = (rec.phone_number or '') + ' / ' + \
                   (rec.mpesa_receipt_number or '')
            res.append((rec.id, name))
        return res

    @api.model
    def create_checkout(self, stk_request, response_params):
        """Create the STK Push Request and store the Merchant/Checkout request details"""
        vals = {}
        if stk_request and response_params:
            vals = dict(
                paybill_number=stk_request.get("BusinessShortCode"), 
                company_id = stk_request.get("company_id"), 
                amount=stk_request.get("Amount"),
                phone_number=stk_request.get("PhoneNumber"),
                payment_reference=stk_request.get("AccountReference"),
                transaction_description=stk_request.get("TransactionDesc"),
                reconciled=False,
                result_code=response_params.get('ResultCode'),
                result_desc=response_params.get('ResultDesc'),
                merchant_request_id=response_params.get('MerchantRequestID'),
                checkout_request_id=response_params.get('CheckoutRequestID'),
            )
            print('STK REQUEST >>> \n', stk_request, 'Vals to save >>>> \n', vals)
            return self.env['mpesa.stk'].sudo().create(vals)
        else:
            return False

    @api.model
    def update_checkout(self, params):
        """
        Stores the payment data for mpesa online as received from safaricom
        via the json CallBackURL
        """
        print('Called UPDATE Checkout >>>', params)
        try:
            if params:
                _checkout_id = params.get('CheckoutRequestID')
                _merchant_id = params.get('MerchantRequestID')
                rec = self.env['mpesa.stk'].search(
                    [('checkout_request_id', '=', _checkout_id), ('merchant_request_id', '=', _merchant_id)])
                print('REC HERE>>>',rec)
                if rec:
                    _bill_ref_number = str(rec.payment_reference).upper()
                    _company_id = rec.company_id.id
                    _result_code = params.get('ResultCode')
                    _result_desc = params.get('ResultDesc')
                    _amount = [x.get('Value') for x in params['CallbackMetadata']['Item'] if
                            x.get('Name') == 'Amount'].pop()
                    _phone_number = [x.get('Value') for x in params['CallbackMetadata']['Item'] if
                                    x.get('Name') == 'PhoneNumber'].pop()
                    _transaction_date = [x.get('Value') for x in params['CallbackMetadata']['Item'] if
                                        x.get('Name') == 'TransactionDate'].pop()
                    _mpesa_receipt_number = [x.get('Value') for x in params['CallbackMetadata']['Item'] if
                                            x.get('Name') == 'MpesaReceiptNumber'].pop()
                    rec.update(
                        {
                            "result_code": _result_code,
                            "result_desc": _result_desc,
                            "amount": _amount,
                            "phone_number": _phone_number,
                            "transaction_date": _transaction_date,
                            "mpesa_receipt_number": _mpesa_receipt_number
                        }
                    )
                    print('Paybill online Completed Successfully')
                    # insert into MPesa Transactions Model
                    # confirm that mpesa transaction id soes not match previous
                        
                    #Set transaction DateTime
                    _dt_trans_time =  datetime(2000, 1, 1)
                    if _transaction_date and len(str(_transaction_date)) == 14:
                        _dt_trans_time = datetime.strptime(str(_transaction_date), '%Y%m%d%H%M%S')
                        _dt_trans_time = _dt_trans_time - timedelta(hours=3) #GMT offset
                    else:
                        _dt_trans_time = datetime(2000, 1, 1)

                    # create mpesa entry
                    values = {
                        'name': _mpesa_receipt_number,
                        'paybill_number': rec.paybill_number,
                        'transaction_type': 'STK Push',
                        'trans_id': _mpesa_receipt_number,
                        'trans_time': _transaction_date,
                        'transaction_date_time': _dt_trans_time,
                        'trans_amount': _amount,
                        'amount_applied': 0,
                        'amount_residual': _amount,
                        'bill_ref_number': _bill_ref_number,
                        'payer_phone_number': _phone_number,
                        'company_id': _company_id,
                        'stk_id':rec.id,
                        # 'payer_name': , #TODO
                        # 'auto_matched': _auto_matched, #TODO
                    }
                    _mpesa_rec = self.env['mpesa.base'].sudo().create(values)
                    print('REC Created', _mpesa_rec, values)
                    return _mpesa_rec
                else:
                    print('Paybill online Failed')
                    return False
            return False
        except Exception as e:
            _logger.warning('Error Completing STK MPesa Transaction: \n' + str(e))
            return False
    
    @api.model
    def update_checkout_error(self, params):
        """
        Stores the Error response for the Payment Checkout
        """
        print('HERE >>>', params)
        try:
            if params:
                _checkout_id = params.get('CheckoutRequestID')
                _merchant_id = params.get('MerchantRequestID')
                
                rec = self.env['mpesa.stk'].search([('checkout_request_id', '=', _checkout_id), ('merchant_request_id', '=', _merchant_id)])
                print ('Rec at ERROR STK >>>', rec)
                if rec:
                    rec.update(
                        {
                            "result_code": params.get('ResultCode'),
                            "result_desc": params.get('ResultDesc'),
                        }
                    )
                    print('Paybill online ERROR Logged Successfully')
                    return True
                else:
                    print('Paybill ERROR LOGGING Failed')
            else:
                print ('No STK Data received to update')
        except Exception as e:
            print('Error Updating Failed STK Transaction >>> \n', e)
            return "Completed"
        finally:
            return "Completed"



class MpesaManualMatch(models.TransientModel):
    _name = 'mpesa.manual.match'
    _description = 'MPesa Manual Match'

    name = fields.Char(string='Record Name')
    company_id = fields.Many2one('res.company', string="Company")
    mpesa_id = fields.Many2one('mpesa.base', 'MPesa Transaction')
    manual_reason = fields.Char(string='Reason for Manual Match')
    partner_id = fields.Many2one('res.partner',string="Customer Account")



    def update_manual_matching(self):
        self.sudo()._update_manual_matching()


    def _update_manual_matching(self):
        for rec in self:
            if rec.mpesa_id.account_payment_id.partner_id and rec.mpesa_id.account_payment_id.partner_id != rec.toilet_name.partner_id :
                raise UserError('Cannot apply payment to a different Customer [' + str(rec.account_payment_id.partner_id.name) + ']')
            if not rec.partner_id:
                raise UserError('The Customer to Match is required')
            
            if rec.partner_id.company_id != rec.mpesa_id.company_id:
                raise UserError('The Customer and MPesa Record must belong to the same Company')

            err_msg = '<pre>' + str(self.env.user.name) + ' has manually matched the MPesa Payment for the following reason:  <ul>'\
                '<li>Reason : ' + str(rec.manual_reason) + '</li>'\
                '<li>Previous Payment Entry : ' +  str(rec.mpesa_id.account_payment_id.name) + '</li>'\
                '</li></ul></pre>'
            rec.mpesa_id.message_post(body=err_msg)

            #update MPesa Record
            rec.mpesa_id.write({
                'partner_id':rec.partner_id,
                'last_processed':datetime.now()
            })

            #search for payment id, if not found create payment entry
            if rec.mpesa_id.account_payment_id:
                _pmt_rec = self.env['account.payment'].search([('id','=',rec.mpesa_id.account_payment_id.id)])
                _pmt_rec.action_draft()
                _pmt_rec.update({
                    'ref' : rec.partner_id.ref,
                    'partner_id' : rec.partner_id
                })
                _pmt_rec.action_post()
            else:
                rec.mpesa_id.create_mpesa_payment_entry(rec.mpesa_id.paybill_number)
             

            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        