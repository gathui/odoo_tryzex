# -*- coding: utf-8 -*-
# from odoo import http


# class CaseFile(http.Controller):
#     @http.route('/case_file/case_file', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/case_file/case_file/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('case_file.listing', {
#             'root': '/case_file/case_file',
#             'objects': http.request.env['case_file.case_file'].search([]),
#         })

#     @http.route('/case_file/case_file/objects/<model("case_file.case_file"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('case_file.object', {
#             'object': obj
#         })
