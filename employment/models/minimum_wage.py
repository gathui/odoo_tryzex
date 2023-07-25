from odoo import models, fields, api,_


class MinimumWage(models.Model):
    _name = 'minimum.wage'
    _description = 'Minimum Wage Orders'

    name =fields.Char(string="Name", default=lambda obj: obj.env['ir.sequence'].next_by_code('minimum.wage'))
    year = fields.Integer(string="Year")
    effective_date = fields.Date(string="Effective Date", help="Date the Minimum Wage Order came into Effect")
    end_date= fields.Date(string="End Date", help="Date the Minimum Wage Order came into Effect")
    job_type = fields.Char(string="Occupation/Job Type/Grade")
    sequence = fields.Integer(string="Job Type Sequence")
    cat_1_per_hr = fields.Float("Cities: Per Hour", help="Cities: Nairobi, Mombasa and Kisumu")
    cat_1_per_day= fields.Float("Cities: Per Day", help="Cities: Nairobi, Mombasa and Kisumu")
    cat_1_per_month= fields.Float("Cities: Per Month", help="Cities: Nairobi, Mombasa and Kisumu")
    cat_2_per_hr= fields.Float("Municipalities: Per Hour", help="Municipalities, Town Councils of Mavoko, Riuru, Limuru")
    cat_2_per_day= fields.Float("Municipalities: Per Day", help="Municipalities, Town Councils of Mavoko, Riuru, Limuru")
    cat_2_per_month= fields.Float("Municipalities: Per Month", help="Municipalities, Town Councils of Mavoko, Riuru, Limuru")
    cat_3_per_hr= fields.Float("All Other: Per Hour", help="All other areas (neither cities nor municipalities nor town councils)")
    cat_3_per_day= fields.Float("All Other: Per Day", help="All other areas (neither cities nor municipalities nor town councils)")
    cat_3_per_month= fields.Float("All Other: Per Month", help="All other areas (neither cities nor municipalities nor town councils)")


    @api.model
    def create(self,vals):
        print('VALSTOSAVE', vals)
        if vals.get('name', ('New')) == ('New'):
            new_name = (_('MW/%s/%s')%(vals['year'],f"{vals['sequence']:02}"))
            vals['name'] = new_name
            
        res = super(MinimumWage,self).create(vals)
        return res
    
    
    @api.model
    def get_jobtype_selection(self):
        strSQL = """SELECT DISTINCT job_type AS val, concat( RIGHT(concat('0',"sequence"),2), ' - ', job_type)AS label 
        FROM minimum_wage  ORDER BY 2;
        """
        
        self._cr.execute(strSQL)
        query_res2 = self._cr.fetchall()
        return query_res2
    

    def name_get(self):
        result = []   
        for rec in self:
            result.append((rec.id, '%s - %s' % (f"{rec.sequence:02}",rec.job_type)))                
                
        return result