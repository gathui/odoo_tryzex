# -*- coding: utf-8 -*-
# from odoo import http


# class SanergyUtils(http.Controller):
#     @http.route('/sanergy_utils/sanergy_utils/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sanergy_utils/sanergy_utils/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sanergy_utils.listing', {
#             'root': '/sanergy_utils/sanergy_utils',
#             'objects': http.request.env['sanergy_utils.sanergy_utils'].search([]),
#         })

#     @http.route('/sanergy_utils/sanergy_utils/objects/<model("sanergy_utils.sanergy_utils"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sanergy_utils.object', {
#             'object': obj
#         })
