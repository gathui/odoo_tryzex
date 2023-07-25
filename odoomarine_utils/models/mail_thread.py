# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import date, timedelta, datetime


class MailThreadInherit(models.AbstractModel):
    _inherit = "mail.thread"

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        for rec in self:
            if rec._name == 'case.file':
                case_file_id = self.env['case.file'].search([('id','=',rec.id)])
                if case_file_id :
                    sms = {
                            "phone_number": case_file_id.claimant_id.phone,
                            "text_message": kwargs['body'],
                            "retry_duration": 1,
                            "scheduled_send_date": datetime.now()+ timedelta(minutes=15),
                            'company_id':case_file_id.company_id.id,
                            'related_record': (_("%s,%s")%(rec._name,rec.id)),
                            'sms_tag':'CASEFILESMS',
                            'active':True
                        }

                print("SENDMSG",rec, rec.id, rec._name,kwargs, kwargs['body'] , '\n', sms)             
                self.env['bulk.sms'].sudo().create(sms)
            return super(MailThreadInherit, rec.with_context(mail_post_autofollow=True)).message_post(**kwargs)