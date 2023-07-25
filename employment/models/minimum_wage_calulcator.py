from odoo import models, fields, api,_
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from dateutil import rrule
from odoo.exceptions import ValidationError,UserError
import calendar
import io
import xlwt
import base64
import xlsxwriter

class EmploymentHistory(models.TransientModel):
    _name = 'employment.history'
    _description = 'Employment History'

    name =fields.Char(string="Name", default=lambda obj: obj.env['ir.sequence'].next_by_code('employment.history'))
    
    min_wage_calc_id = fields.Many2one('minimum.wage.calculator', string="Calculator ID")
    occupation_name = fields.Selection(selection=lambda self: self.env['minimum.wage'].get_jobtype_selection(),
                                       default=lambda self: self.min_wage_calc_id.job_type,
                                       string="Occupation/Job Type/Grade")
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    job_grade_id = fields.Many2one('minimum.wage',string = "Job Grade")
    monthly_salary = fields.Float(string="Monthly Salary")

    @api.onchange('occupation_name')
    def onchange_occupation_name(self):
        for rec in self:
            rec.min_wage_calc_id = self.env['minimum.wage'].search([('job_type','=', rec.occupation_name)],limit=1)


class MonthlySalary(models.TransientModel):
    _name = 'monthly.salary'
    _description = 'Monthly Salary Computation'

    name =fields.Char(string="Name", default=lambda obj: obj.env['ir.sequence'].next_by_code('monthly.salary'))
    min_wage_calc_id = fields.Many2one('minimum.wage.calculator', string="Calculator ID")
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    occupation_name = fields.Char(string = "Occupation", related="effective_wage_order_id.job_type")
    effective_wage_order_id = fields.Many2one('minimum.wage',string = "Effective Wage Order")
    monthly_salary = fields.Float(string="Monthly Salary")
    minimum_wage = fields.Float(string="Minimum Wage")
    wage_variance = fields.Float(string="Wage Variance")


class MinimumWage(models.TransientModel):
    _name = 'minimum.wage.calculator'
    _description = 'Minimum Wage Calculator'
    _inherit = ['mail.thread','mail.activity.mixin']

    name =fields.Char(string="Name", default=lambda obj: obj.env['ir.sequence'].next_by_code('minimum.wage.calculator'))
    region  = fields.Selection([
        ('cat_1', 'Cities: Nairobi, Mombasa and Kisumu'),
        ('cat_2', 'Municipalities, Town Councils of Mavoko, Riuru, Limuru'),
        ('cat_3', 'All other areas (neither cities nor municipalities nor town councils)'),
    ], string='Region', help="Region")
    job_type = fields.Selection(selection=lambda self: self.env['minimum.wage'].get_jobtype_selection(),string="Occupation/Job Type/Grade")
    employment_history_ids = fields.One2many('employment.history', 'min_wage_calc_id', string="Employment History")
    monthly_salary_ids = fields.One2many('monthly.salary', 'min_wage_calc_id', string="Monthly Salary")
    year = fields.Integer(string="Year")
    effective_date = fields.Date(string="Effective Date", help="Date the Minimum Wage Order came into Effect")
    end_date= fields.Date(string="End Date", help="Date the Minimum Wage Order came into Effect")
    # job_type = fields.Char(string="Job Type/Grade")
    sequence = fields.Integer(string="Job Type Sequence")

        
    @api.onchange('job_type')
    def _onchange_jobgrade(self):
        print('job_type', self.job_type)

    def compute_monthly_wages(self):
        for rec in self:
            rec.monthly_salary_ids.unlink()
            for hist in rec.employment_history_ids:
                active_years = [year for year in range( hist.start_date.year-1,hist.end_date.year + 1)]
                print('active_years', active_years, hist.job_grade_id.job_type)
                min_wage_order_ids = self.env['minimum.wage'].search([('job_type','=',hist.job_grade_id.job_type),
                                                                      ('year','in', active_years)
                                                                      ])
                print('min_wage_order_ids', hist, '\n',min_wage_order_ids,'\n', hist.start_date,hist.end_date,hist.occupation_name,hist.job_grade_id.job_type)
                monthly_emp = []
                for dt in rrule.rrule(rrule.MONTHLY, dtstart=hist.start_date, until=hist.end_date):
                    mth_start_date = dt.date().replace(day=1)
                    mth_start_date = mth_start_date if mth_start_date > hist.start_date else hist.start_date
                    mth_end_date =  dt.date() + relativedelta(day=32)
                    mth_end_date = mth_end_date if mth_end_date < hist.end_date else hist.end_date
                    
                    effective_wage_order = min_wage_order_ids.filtered(lambda line: line.effective_date <= dt.date()
                                                                       and line.end_date >= mth_end_date )
                    print('effective_wage_order',effective_wage_order)
                    region_category = (_("%s_per_month")%(self.region))
                    vals = {
                            "min_wage_calc_id" : rec.id,
                            "start_date" : mth_start_date,
                            "end_date" : mth_end_date,
                            # "job_grade_id" : hist.job_grade_id.id,
                            "effective_wage_order_id" : effective_wage_order[0]['id'] if len(effective_wage_order) > 0 else None,
                            "monthly_salary" : hist.monthly_salary,
                            "minimum_wage" : effective_wage_order[0][region_category] if len(effective_wage_order) > 0 else None,
                            "wage_variance" : effective_wage_order[0][region_category] - hist.monthly_salary if len(effective_wage_order) > 0 else None,
                        }
                    
                    monthly_emp.append(vals)
                    print('\n',vals)
                self.env['monthly.salary'].create(monthly_emp)

    def export_to_excel(self):
        file_name = 'Minimum Wage Calculation -' + str(date.today().strftime("%Y%m%d%H%M%S"))

        workbook = xlwt.Workbook()
            
        normal_left = xlwt.easyxf('font:bold False;align: horiz left;align: vert center')
        normal_center = xlwt.easyxf('font:bold False;align: horiz center;align: vert center')
        normal_right = xlwt.easyxf('font:bold False;align: horiz right;align: vert center')
        bold_center = xlwt.easyxf('font:height 225,bold True;pattern: pattern solid,fore_colour gray25;align: horiz center;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40')
        number_left = xlwt.easyxf("font:bold False;align: horiz left;align: vert center", "####")
        worksheet = workbook.add_sheet(u'Sheet1',cell_overwrite_ok=True)

        worksheet.col(0).width = 8000
        worksheet.col(1).width = 8000
        worksheet.col(2).width = 4800
        worksheet.col(3).width = 4800
        worksheet.col(4).width = 5500
        worksheet.col(5).width = 5500
        # worksheet.col(6).width = 8000
        # worksheet.col(7).width = 8000
        
        worksheet.write(0, 0, "Sequence", bold_center)
        worksheet.write(0, 1, "Start Date", bold_center)
        worksheet.write(0, 2, "End Date", bold_center)
        worksheet.write(0, 3, "Monthly Salary", bold_center)
        worksheet.write(0, 4, "Minimum Wage", bold_center)
        worksheet.write(0, 5, "Wage Variance", bold_center)
        # worksheet.write(0, 6, "PAYMENT DETAILS", bold_center)
        # worksheet.write(0, 7, "EMAIL ADDRESS", bold_center)
        # worksheet.write(0, 8, "POP", bold_center)
                            
        row_index = 1

        for rec in self.monthly_salary_ids:
            worksheet.row(row_index).height = 350
            worksheet.write(row_index, 0, row_index, normal_left)
            worksheet.write(row_index, 1, rec.start_date.strftime("%Y-%m-%d") or "", normal_left)
            worksheet.write(row_index, 2, rec.end_date.strftime("%Y-%m-%d") or "", normal_left)
            worksheet.write(row_index, 3, rec.monthly_salary or "", normal_left)
            worksheet.write(row_index, 4, rec.minimum_wage, normal_left)
            worksheet.write(row_index, 5, rec.wage_variance, normal_right)
            # worksheet.write(row_index, 6, str(rec.move_ids), normal_left)
            # worksheet.write(row_index, 7, "", normal_left)
            # worksheet.write(row_index, 8, "051", normal_center)
            
            row_index = row_index + 1


        fp = io.BytesIO()
        workbook.save(fp)
        data = base64.encodestring(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        attachment_vals = {
            "name": str(file_name) + ".xls",
            "res_model": "ir.ui.view",
            "type": "binary",
            "datas": data,
            "public": True,
        }
        
        fp.close()

        attachment = IrAttachment.search(
            [('name', '=', str(file_name) ),
            ('type', '=', 'binary'), ('res_model', '=', 'ir.ui.view')],
            limit=1)
        if attachment:
            attachment.write(attachment_vals)
        else:
            attachment = IrAttachment.create(attachment_vals)
            attachment_id = attachment.id
        #TODO: make user error here
        if not attachment:
            raise UserError('There is no attachments...')
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        download_url = '/web/content/' + str(attachment_id) + '?download=true'
        # download
        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "new",
        }

    def createxl(self):
        # Create an new Excel file and add a worksheet.
        workbook = xlsxwriter.Workbook('demo.xlsx')
        worksheet = workbook.add_worksheet()

        # Widen the first column to make the text clearer.
        worksheet.set_column('A:A', 20)

        # Add a bold format to use to highlight cells.
        bold = workbook.add_format({'bold': True})

        # Write some simple text.
        worksheet.write('A1', 'Hello')

        # Text with formatting.
        worksheet.write('A2', 'World', bold)

        # Write some numbers, with row/column notation.
        worksheet.write(2, 0, 123)
        worksheet.write(3, 0, 123.456)

        # # Insert an image.
        # worksheet.insert_image('B5', 'logo.png')

        workbook.close()