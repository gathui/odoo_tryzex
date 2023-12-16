from odoo import models, fields, api,_
from odoo.exceptions import ValidationError,UserError
import requests
from datetime import date, datetime,timedelta

import logging
_logger = logging.getLogger(__name__)

class CaseOutcome(models.Model):
    _name = 'case.outcome'
    _description = 'Case Outcome'
    _order = "name asc"
    _check_company_auto = True

    name=fields.Char(string="Case Outcome", )
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    active = fields.Boolean(string="Active", default=True)
    
 
class CaseFileCategory(models.Model):
    _name = 'case.file.category'
    _description = 'Case File Category'
    _order = "name asc"
    _check_company_auto = True

    name=fields.Char(string="Category Name", )
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    code = fields.Char(string='Code', help="Short Code that will be appended to Case Files eg EMP for Employment cases will create a Case File ID EMP/2000/01/01")
    active = fields.Boolean(string="Active", default=True)
    subcategory_ids = fields.One2many('case.file.subcategory','category_id', string="Sub Categories")
    document_type_ids = fields.One2many('case.document.type','category_id', string="Document Types")


class CaseFileSubCategory(models.Model):
    _name = 'case.file.subcategory'
    _description = 'Case File Sub Category'
    _order = "name asc"
    _check_company_auto = True

    name=fields.Char(string="Sub-Category Name", )    
    category_id = fields.Many2one('case.file.category', string="Category")
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    active = fields.Boolean(string="Active", default=True)
    document_type_ids = fields.One2many('case.document.type','subcategory_id', string="Document Types")
    
class CaseReference(models.Model):
    _name = 'case.reference'
    _description = 'Case Reference Numbers'
    _order = "name asc"
    _check_company_auto = True

    reference=fields.Char(string="Reference", default=lambda obj: obj.env['ir.sequence'].next_by_code('case.reference'))
    case_file_id = fields.Many2one('case.file', string="Case File", check_company=True, domain="[('company_id', '=', company_id)]")
    name=fields.Char(string="Reference Number", help="Reference Number given by external entity associated with this Case File")
    court_id = fields.Many2one('court',string="Court")
    institution=fields.Char(string="Institution", help="Institution that provided the Reference Number eg Court, Police Station, Academic Institution, Government Body etc")
    comments=fields.Char(string="Comments", )
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    active = fields.Boolean(string="Active", default=True)
   
class CaseFile(models.Model):
    _name = 'case.file'
    _description = 'Case File'
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = "name asc"
    _check_company_auto = True

    name=fields.Char(string="Name", default=lambda obj: obj.env['ir.sequence'].next_by_code('case.file'))

    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    claimant_id = fields.Many2one('res.partner', string = "Claimant", check_company=True, 
                                  domain="[('company_id', '=', company_id)]")
    respondent_ids = fields.One2many('case.contact', 'case_file_id', string = "Respondent(s)", 
                                      compute="_fetch_case_contacts")
    opposing_counsel_ids = fields.One2many('case.contact', 'case_file_id', string = "Opposing Counsel(s)", 
                                      compute="_fetch_case_contacts")
    reference = fields.Char('Reference')
    case_number = fields.Char('Case Number')
    tracking_number = fields.Char('Tracking Number')
    citation_reference = fields.Char('Citation')
    ob_number = fields.Char('OB Number')
    case_commentary = fields.Char('Commentary', help="Top level commmentary about the case. For more detailed information, enter in the Details under the details tab")
    details = fields.Text('Details')
    case_type = fields.Selection([
        ('civil', 'Civil'),
        ('criminal', 'Criminal'),
    ], string='Case Type', help="Case Type", group_expand='_expand_states',)
    category_id = fields.Many2one('case.file.category', string="Category", check_company=True, domain="[('company_id', '=', company_id)]")
    subcategory_id = fields.Many2one('case.file.subcategory', string="Sub Category", check_company=True,domain="[('company_id', '=', company_id)]")
    state = fields.Selection([
        ('Open', 'Open'),
        ('Closed', 'Closed'),
        ('Canceled', 'Canceled')
    ], string='Status', default='Open', help="Status of the Case.", group_expand='_expand_states',tracking=True)
    case_outcome_id = fields.Many2one('case.outcome', string="Case Outcome", check_company=True, domain="[('company_id', '=', company_id)]")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date", tracking=True)
    case_contact_ids = fields.One2many('case.contact','case_file_id', string="Case Contact", check_company=True, domain="[('company_id', '=', company_id)]")
    case_document_ids = fields.One2many('case.document', 'case_file_id', string = "Case Documents", check_company=True, domain="[('company_id', '=', company_id)]")
    case_reference_ids = fields.One2many('case.reference','case_file_id', string="Case References", check_company=True, domain="[('company_id', '=', company_id)]")
    case_invoice_ids = fields.One2many('account.move', 'case_file_id', string = "Case Invoices", check_company=True, domain="[('company_id', '=', company_id)]")
    case_expense_ids = fields.One2many('hr.expense', 'case_file_id', string = "Case Expenses", check_company=True, domain="[('company_id', '=', company_id)]")
    total_expenses = fields.Monetary(string="Total Expenses", currency_field = 'currency_id', compute="_compute_expenses",help="Total Expenses Amount")
    total_invoices = fields.Monetary(string="Total Invoices", currency_field = 'currency_id', compute="_compute_invoices",help="Total Invoiced Amount")
    total_invoice_balance = fields.Monetary(string="Invoice Balance", currency_field = 'currency_id',help="Total Invoiced Amount Owed")
    total_income = fields.Monetary(string="Total Income", currency_field = 'currency_id',help="Total Income Realised from this Case File", compute="_compute_income")
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.company.currency_id.id)
    overdue_tasks = fields.Integer(string="Overdue Tasks", compute="_compute_tasks")
    tasks_today = fields.Integer(string="Today's Tasks", compute="_compute_tasks")
    case_act_ids = fields.Many2many('case.act',string="Case Acts")
    billing_type = fields.Selection([
        ('fixed', 'Fixed Fee'),
        ('per_hour', 'Per Hour'),
        ('expenses_only', 'Expenses Only'),
        ('probono', 'Pro Bono')
    ], string='Billing Type',  help="Billing Method", group_expand='_expand_states',tracking=True)

    missing_doc_types = fields.Char(string="Missing Docs", compute="_compute_missing_documents")

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]
    
    def _fetch_case_contacts(self):
        for rec in self:
            rec.respondent_ids = self.env['case.contact'].search([('company_id', '=', rec.company_id.id),('case_file_id','=',rec.id),('contact_type','=','respondent')])
            rec.opposing_counsel_ids = self.env['case.contact'].search([('company_id', '=', rec.company_id.id),('case_file_id','=',rec.id),('contact_type','=','opposing_counsel')])
            # print('_fetch_case_contacts', rec.company_id.id, rec.id, rec.respondent_ids,rec.opposing_counsel_ids)
    
    def _compute_tasks(self):
        for rec in self:
            rec.overdue_tasks = self.env['mail.activity'].search_count([('res_model','=','case.file'),('res_id','=',rec.id),
                                                                    ('date_deadline','<',date.today())])
            rec.tasks_today = self.env['mail.activity'].search_count([('res_model','=','case.file'),('res_id','=',rec.id),
                                                                    ('date_deadline','=',date.today())])

    @api.onchange('category_id')
    def _onchange_category_id(self):
        for rec in self:
            rec.subcategory_id = None


    @api.model
    def create(self,vals):
        if vals.get('name', ('New')) == ('New'):
            company_prefix = self.env.company.case_file_prefixcode or 'AA'
            category_id = self.env['case.file.category'].search([('id','=',vals['category_id'])])
            category_code = category_id.code if category_id else 'ZZZ'
            next_sequence = self.env['ir.sequence'].next_by_code('case.file') or ('New')
            new_name = (_('%s/%s/%s')%(company_prefix,category_code,next_sequence))
            vals['name'] = new_name
            
        res = super(CaseFile,self).create(vals)
        return res
    
    def compute_missing_documents(self):
        msg = self._compute_missing_documents()
        if msg:
            raise UserError(msg)
        
    def _compute_missing_documents(self):
        for rec in self:
            required_docs = self.env['case.document.type'].search([('required','=',True), ('active','=',True), 
                                                                   ('category_id','=',rec.category_id.id),'|',
                                                                   ('subcategory_id','=',rec.subcategory_id.id),
                                                                   ('apply_to_all','=',True)
                                                                   ])
            
            print("required_docs",required_docs, required_docs.ids)
            file_docs = rec.case_document_ids.filtered(lambda line: line.document_type_id.required == True)
            print("file_docs",file_docs, file_docs.ids)
            set_required_docs = set(required_docs.ids)
            set_current_docs = set(file_docs.ids)
            print("SETS",set_required_docs, set_current_docs)
            missing_doc_type_ids = set_required_docs.difference(set_current_docs)
            print("missing_doc_type_ids",missing_doc_type_ids)
            if len(missing_doc_type_ids) > 0:
                missing_recs = self.env['case.document.type'].search([('required','=',True), ('active','=',True), 
                                                                   ('id','in',list(missing_doc_type_ids))],order="sequence")
                print('MISSINGRECS', missing_recs)
                msg = (_("The following Document Types are required for the '%s' Case Subcategory:") % (rec.subcategory_id.name))
                counter = 1
                for missing_rec in missing_recs:
                    msg = (_("%s\n\t%s: %s")%(msg,counter, missing_rec.name))
                    counter = counter + 1

                rec.missing_doc_types = _(("%s/%s")%(len(missing_recs),len(set_required_docs)))
                return msg
            else:
                rec.missing_doc_types = ""
                return False
            

    def action_create_invoice(self):        
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Create Invoice'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,#
            'nodestroy':True,
            'target': 'new',
            'context': dict(self._context, 
                            default_move_type='out_invoice',
                            default_partner_id = self.claimant_id.id,
                default_case_file_id = self.id,
                default_invoice_date = date.today(),
                default_payment_reference = self.name
                )
        }
        return action
    
    def action_create_claimant(self):        
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Create Expense'),
            'res_model': 'hr.expense',
            'view_mode': 'form',
            'view_id': self.env.ref('hr_expense.hr_expense_view_form').id,
            'nodestroy':True,
            'target': 'new',
            'context': dict(self._context, default_partner_id = self.claimant_id.id,
                default_case_file_id = self.id,
                default_invoice_date = date.today(),
                default_payment_reference = self.name
                )
        }
        return action
    
    def action_create_expense(self):        
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Create Expense'),
            'res_model': 'hr.expense',
            'view_mode': 'form',
            'view_id': self.env.ref('hr_expense.hr_expense_view_form').id,
            'nodestroy':True,
            'target': 'new',
            'context': dict(self._context, default_partner_id = self.claimant_id.id,
                default_case_file_id = self.id,
                default_invoice_date = date.today(),
                default_payment_reference = self.name
                )
        }
        return action

    def _compute_expenses(self):
        for rec in self:
            total_amount = 0
            for exp in rec.case_expense_ids.filtered(lambda line: line.state != "refused"):
                total_amount = total_amount + exp.total_amount
            
            rec.total_expenses = total_amount


    def _compute_invoices(self):
        for rec in self:
            total_amount = 0
            total_balance = 0
            for inv in rec.case_invoice_ids.filtered(lambda line: line.state != "cancel"):
                total_amount = total_amount + inv.amount_total
                total_balance = total_balance + inv.amount_residual
            
            rec.total_invoices = total_amount
            rec.total_invoice_balance = total_balance


    @api.depends('total_invoices','total_expenses')
    def _compute_income(self):
        for rec in self:
            rec.total_income = rec.total_invoices - rec.total_expenses

    
    def action_do_nothing(self):
        print('nothing')


    def action_close_case(self):
        for rec in self:
            rec.update({"state":'Closed', "end_date":date.today()})

    def action_cancel_case(self):
        for rec in self:
            rec.update({"state":'Canceled', "end_date":date.today()})

    def action_reopen_case(self):
        for rec in self:
            rec.update({"state":'Open'})


class MailActivityInherit(models.AbstractModel):
    _inherit = "mail.activity"
    
    starting_time = fields.Datetime(string="Starting At")
    duration = fields.Float(string="Duration")

    @api.model
    def create(self,vals):
        try:
            start_time = datetime.strptime(vals['starting_time'], "%Y-%m-%d %H:%M:%S")
            print('STARTTIME',vals['starting_time'])
            # event_time = (_("%s %s"))%(str(vals['date_deadline']), str(vals['start_time']))
            # event_time = date.strftime("%Y-%m-%d %H:%M:%S")
            print('CREATEMAILMIXIN', vals, )
            cal_vals={"user_id":vals['user_id'],
                "res_id": vals['res_id'],
                "res_model_id": vals['res_model_id'],
                "name": vals['summary'],
                "active": True,
                "privacy":'public',
                "show_as":'busy',
                "start": start_time,
                "stop": start_time + timedelta(hours=self.duration or 1),
                "duration":self.duration or 1,
                "allday":False,
                "follow_recurrence":False
                }
            cal = self.env['calendar.event'].create(cal_vals)
            vals['calendar_event_id']=cal.id
            vals['deadline'] = start_time
        except Exception as e:
            print('Could not create calendar event', e)

        return super(MailActivityInherit, self).create(vals)
    
    def write(self,vals):
        for rec in self:
            print('WRITEMAILMIXIN',rec.id, vals)
            return super(MailActivityInherit, self).write(vals)