from odoo import models, fields, api


class CourtRank(models.Model):
    _name = 'court.rank'
    _description = 'Court Rank'
    _inherit = ['mail.thread','mail.activity.mixin']
    

    name=fields.Char(string="Name", )
    rank = fields.Integer(string="Court Rank")


class Court(models.Model):
    _name = 'court'
    _description = 'Courts'
    _inherit = ['mail.thread','mail.activity.mixin']
    

    reference=fields.Char(string="Reference", default=lambda obj: obj.env['ir.sequence'].next_by_code('court'))
    name=fields.Char(string="Name", )
    court_rank_id = fields.Many2one('court.rank',string="Court Rank")
    county_id = fields.Many2one('ke.county', 'County')
    subcounty_id = fields.Many2one('ke.subcounty', 'Sub-County')

    
    def name_get(self):
        result = []   
        for rec in self:
            result.append((rec.id, '%s - %s - %s' % (str(rec.court_rank_id.name),str(rec.county_id.name),str(rec.name))))                
                
        return result



# class CourtAppearnaceType(models.Model):
#     _name = 'court.appearance.type'
#     _description = 'Court Appearance Type'
#     _order = "name asc"
#     _check_company_auto = True

#     name=fields.Char(string="Category Name", )
#     company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
#     code = fields.Char(string='Code', help="Short Code that will be appended to Case Files eg EMP for Employment cases will create a Case File ID EMP/2000/01/01")
#     active = fields.Boolean(string="Active", default=True)
#     subcategory_ids = fields.One2many('case.file.subcategory','category_id', string="Sub Categories")
#     document_type_ids = fields.One2many('case.document.type','category_id', string="Document Types")

# class CourtAppearance(models.Model):
#     _name = 'court.appearance'
#     _description = 'Courts'
#     _inherit = ['mail.thread','mail.activity.mixin']
    

#     reference=fields.Char(string="Reference", default=lambda obj: obj.env['ir.sequence'].next_by_code('court'))
#     name=fields.Char(string="Name", )
#     court_id = fields.Many2one('court',string="Court Name")
#     county_id = fields.Many2one('ke.county', 'County')
#     subcounty_id = fields.Many2one('ke.subcounty', 'Sub-County')