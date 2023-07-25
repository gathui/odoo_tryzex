from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)

class ke_county(models.Model):
    _name = 'ke.county'
    _description = 'Counties - Kenya'

    name=fields.Char(string="Name", )
    code = fields.Char(string="Code")
    
    def name_get(self):
        result = []   
        for rec in self:
            result.append((rec.id, '%s - %s' % (str(rec.code),str(rec.name))))                
                
        return result
        
class ke_subcounty(models.Model):
    _name = 'ke.subcounty'
    _description = 'Sub Counties - Kenya'

    name=fields.Char(string="Name", )
    code = fields.Char(string="Code")
    county_id = fields.Many2one('ke.county', 'County')
    
    def name_get(self):
        result = []   
        for rec in self:
            result.append((rec.id, '%s - %s' % (str(rec.code),str(rec.name))))                
                
        return result