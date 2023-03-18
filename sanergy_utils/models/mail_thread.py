# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


class MailThreadInherit(models.AbstractModel):
    _inherit = "mail.thread"

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        for rec in self:
            followers = self.env['mail.followers'].sudo().search([
                ('res_model', '=', rec._name),
                ('res_id', '=', rec.id),
                ('partner_id', '!=', False)
            ])
            
            try:
                if followers and rec._name and 'partner_id' in self.env[rec._name]._fields :
                    for follower in followers:
                        if follower.partner_id == rec.partner_id:
                            partner_ids = []
                            partner_ids.append(follower.partner_id.id)
                            rec.message_unsubscribe(partner_ids)
            except Exception as e:
                print('Error Updating Followers')
            
            return super(MailThreadInherit, rec.with_context(mail_post_autofollow=True)).message_post(**kwargs)