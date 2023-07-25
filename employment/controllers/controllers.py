# -*- coding: utf-8 -*-
# from odoo import http


# class Employment(http.Controller):
#     @http.route('/employment/employment', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/employment/employment/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('employment.listing', {
#             'root': '/employment/employment',
#             'objects': http.request.env['employment.employment'].search([]),
#         })

#     @http.route('/employment/employment/objects/<model("employment.employment"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('employment.object', {
#             'object': obj
#         })
