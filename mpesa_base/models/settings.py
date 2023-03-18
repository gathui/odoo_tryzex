import string
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MPesaCustomSettings(models.Model):
    """ MPesa Custom Settings
    """
    _name = 'mpesa.settings'
    _description = 'Hold common setting fields required by Mpesa Base module'

    name = fields.Char(string="Record Name", default=lambda obj: obj.env['ir.sequence'].next_by_code('mpesa.settings'))
    company_id = fields.Many2one('res.company', string="Company ID")
    paybill_number = fields.Char(string="Paybill Number" )
    mpesa_app = fields.Selection([('slk_ocs_sales','Regen Organics - OCS Sales'),('mtaa_fresh','Fresh Life - Mtaa Fresh')], string="MPesa App", help="Application that the Paybill is being created for")

    # auth_passkey = fields.Char(string="Auth Passkey" )
    authorisation_url = fields.Char(string="Authorisation URL")

    consumer_key = fields.Char(string="Consumer Key", password="True")
    consumer_secret = fields.Char(string="Consumer Secret" , password="True")

    stk_confirmation_url = fields.Char(string="STK Confirmation URL")
    stk_push_url = fields.Char(string="STK Push URL")
    mpesa_express_pass_key = fields.Char(string="MPesa Express Pass Key" , password="True")
    mpesa_express_url = fields.Char(string="MPesa Express URL")

    c2b_confirmation_url = fields.Char(string="C2B Confirmation URL")
    validation_url = fields.Char(string="Validation URL")

    journal_id = fields.Many2one('account.journal',string="MPesa Journal ID")
    ar_account_id = fields.Many2one('account.account', string="AR Account ID")
    active = fields.Boolean(string="Active", default=True)
