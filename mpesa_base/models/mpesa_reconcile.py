# -*- coding: utf-8 -*-
import tempfile
import binascii
import xlrd
import logging
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo import models, fields, api, tools, _
_logger = logging.getLogger(__name__)

try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')



class MpesaReconcile(models.Model):
    _name = "mpesa.reconcile"
    _description = 'MPesa Reconcile Model'

    recon_wizard_id = fields.Many2one('mpesa.reconcile.import', string="Recon Wizard ID")
    paybill_number = fields.Char(string="Paybill Number")
    company_id = fields.Many2one('res.company', string="Company")
    reference = fields.Integer(string='Row Number')
    trans_id = fields.Char(string='Record Name')
    transaction_type = fields.Char(string='Transaction Type')
    transaction_date_time = fields.Datetime(string="Transaction Date")
    trans_amount = fields.Integer(string='Transaction Amount')
    bill_ref_number = fields.Char(string='Bill Ref Number')
    payer_name = fields.Char(string='Payer Name')
    payer_phone_number = fields.Char(string='Phone Number')
    trans_details = fields.Char(string='Transaction Details')  



class MpesaReconcileImport(models.Model):
    _name = "mpesa.reconcile.import"
    _description = 'MPesa Reconcile Import Wizard'

    name = fields.Char(string='Name', default=lambda obj: obj.env['ir.sequence'].next_by_code('mpesa.reconcile.import'))    
    paybill_number = fields.Char(string="Paybill Number")
    company_id = fields.Many2one('res.company', string="Company")
    file = fields.Binary(string='File')
    import_option = fields.Selection([('xls', 'MPesa Import File (Excel File Only)')], string='Select', default='xls')
    mpesa_recon_record_ids = fields.One2many('mpesa.reconcile','recon_wizard_id', string="MPesa Recon Records")
    missing_recon_ids = fields.One2many('mpesa.reconcile.view', 'recon_wizard_id', string="Missing Records", compute="_get_missing_recon_ids")
    error_mpesa_record_ids = fields.Many2many('mpesa.base', string="Erroneous MPesa Records", compute = "_get_erroneous_records")


    @api.depends('paybill_number')
    def _get_erroneous_records(self):
        if not self.paybill_number:
            self.error_mpesa_record_ids = None
            return

        strSQL = """SELECT id--, trans_id, toilet_id, deposit_invoice_id, transaction_date_time,trans_amount, bill_ref_number 
                FROM 
                (
                    SELECT id, trans_id, trans_amount, transaction_date_time at time zone 'UTC' transaction_date_time
                    FROM mpesa_base
                    WHERE paybill_number = '%s'
                ) t 
                WHERE transaction_date_time::date
                BETWEEN 
                (SELECT MIN(transaction_date_time::date at time zone 'UTC') FROM mpesa_reconcile WHERE paybill_number = '%s') AND 
                (SELECT MAX(transaction_date_time::date at time zone 'UTC') FROM mpesa_reconcile WHERE paybill_number = '%s')
                AND trans_id NOT IN
                (
                    SELECT trans_id 
                    FROM mpesa_reconcile 
                    WHERE transaction_date_time::date BETWEEN 
                    (SELECT MIN(transaction_date_time::date at time zone 'UTC') FROM mpesa_reconcile WHERE paybill_number = '%s') AND 
                    (SELECT MAX(transaction_date_time::date at time zone 'UTC') FROM mpesa_reconcile WHERE paybill_number = '%s')
                )
                AND trans_amount > 0
                """ % (self.paybill_number,self.paybill_number,self.paybill_number,self.paybill_number,self.paybill_number)
                
        self._cr.execute(strSQL)
        query_res = self._cr.dictfetchall()
        
        vals = []
        if query_res:
            for rec in query_res:
                vals.append(rec.get('id'))

            self.write({'error_mpesa_record_ids':[(6,0,vals)]})
        else:
            self.error_mpesa_record_ids= None

    @api.depends('paybill_number')
    def _get_missing_recon_ids(self):
        if not self.paybill_number:
            self.missing_recon_ids = None
            return

        strSQL = """SELECT id, recon_wizard_id, paybill_number, company_id,reference, trans_id, transaction_type, transaction_date_time,
            trans_amount, bill_ref_number, payer_name,payer_phone_number,trans_details
            FROM mpesa_reconcile 
            WHERE paybill_number = '%s' AND trans_id NOT IN 
            (
                SELECT trans_id 
                FROM 
                (
                    SELECT trans_id, transaction_date_time at time zone 'UTC' transaction_date_time
                    FROM mpesa_base
                    WHERE paybill_number = '%s'
                ) t
                WHERE transaction_date_time::date BETWEEN 
                (SELECT MIN(transaction_date_time::date at time zone 'EAT') FROM mpesa_reconcile WHERE paybill_number = '%s') AND 
                (SELECT MAX(transaction_date_time::date at time zone 'EAT') FROM mpesa_reconcile WHERE paybill_number = '%s')
            )
            ORDER BY reference
        """ % (self.paybill_number,self.paybill_number,self.paybill_number,self.paybill_number)
        
        print(strSQL)
        self._cr.execute(strSQL)
        query_res = self._cr.dictfetchall()
        
        vals = []
        if query_res:
            for rec in query_res:
                vals.append(rec.get('id'))

            self.write({'missing_recon_ids':[(6,0,vals)]})
        else:
            self.missing_recon_ids= None

    def import_mpesa_entries(self):
        
        print('Initiated import process')
        res = []
        
        fx = tempfile.NamedTemporaryFile(suffix=".xlsx")
        fx.write(binascii.a2b_base64(self.file))
        fx.seek(0)
        values = {}
        workbook = xlrd.open_workbook(fx.name)
        sheet = workbook.sheet_by_index(0)

        _paybill_number = None
        _company_id = None
        print('Initiated import process again')
        if sheet:
            _paybill_number = sheet.cell(1,1).value
            try:
                # convert to string without decimals
                _paybill_number = str(int(float(_paybill_number)))
            except Exception:
                _paybill_number = False

            print('Paybill number loaded', _paybill_number)

            rec = self.env['mpesa.settings'].sudo().search([('paybill_number','=',_paybill_number),
            ('active','=',True)],limit=1)

            if not rec:
                raise ValidationError('No Active Paybill Number found: ' +str(_paybill_number))
                
            _company_id = rec.company_id
            
            for row_no in range(7,sheet.nrows):
                if row_no <= 0:
                    field = map(lambda row: row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    mpesa_line = list(map(lambda row: str(row.value), sheet.row(row_no)))
                    string_dt = str(mpesa_line[1])

                    def convert_to_float(value):
                        try:
                            float(value)
                            return True
                        except ValueError:
                            return False

                    if convert_to_float(string_dt):
                        datetime_xlt = datetime(*xlrd.xldate_as_tuple(float(string_dt), workbook.datemode))
                        # string_dt = datetime_xlt.datet#ime().strftime('%d/%m/%Y')
                    
                    _trans_amount = 0
                    _trans_amount = int(float(mpesa_line[5] or 0))
                    # print(str(row_no) + ' | ' + str(mpesa_line[0] + ' | ' + str(_trans_amount) + ' | ' +  str(string_dt) + ' | '+  str(datetime_xlt) + ' | ' + str(mpesa_line[12])))
                    if str(mpesa_line[10]) and str(mpesa_line[10]).find(' - '):
                        _trans_detail = str(mpesa_line[10])
                        _payer_phone_number =  _trans_detail[:_trans_detail.find(' - ')]
                        _payer_name = _trans_detail[_trans_detail.find(' -')+3:]
                    else:
                        _payer_phone_number =  '254700000000'
                        _payer_name = '*JOHN DOE*'

                    res.append({
                        'recon_wizard_id':self.id,
                        'paybill_number':_paybill_number,
                        'company_id': _company_id.id,
                        'payer_name': _payer_name,
                        'trans_id': str(mpesa_line[0]).upper(),
                        'transaction_type': str(mpesa_line[9]),
                        'transaction_date_time': datetime_xlt,
                        'trans_amount': _trans_amount,
                        'bill_ref_number': str(mpesa_line[12]),
                        'payer_name':_payer_name,
                        'payer_phone_number': _payer_phone_number,
                        'trans_details': _payer_name,
                    })

            if res:
                #delete existing records in reconcile model
                recon_records = self.env['mpesa.reconcile'].search([('paybill_number','=',_paybill_number)])
                recon_records.unlink()
                #insert new records
                mpesa_recs = self.env['mpesa.reconcile'].sudo().create(res)

                #update phone and first names
                self.update_phone_and_trans_details()
            
            #reload wizard
            return {
                'name':_("Step 2: Reconcile Entries"),
                'view_mode': 'form',
                'view_id': self.env.ref('mpesa_base.mpesa_reconcile_import_form_view').id,
                # 'view_type': 'form',
                'res_model': 'mpesa.reconcile.import',
                'type': 'ir.actions.act_window',
                # 'target': 'new',
                'res_id':self.id,
                'context':dict(self._context, create=False, default_recon_wizard_id=self.id, default_paybill_number=_paybill_number, default_company_id=_company_id),
            }


    def update_phone_and_trans_details(self):
        #use the details from the paybill doc to update phone and names
        strSQL = """UPDATE mpesa_base m
                    SET "payer_phone_number" = t.payer_phone_number, payer_name = t.payer_name, 
                    transaction_type = t.transaction_type
                    FROM
                    (
                        SELECT m.id, m.trans_id, r.payer_name, r.payer_phone_number, r.transaction_type
                        FROM mpesa_base m
                        INNER JOIN mpesa_reconcile r
                        ON m.trans_id = r.trans_id
                        WHERE COALESCE(m.trans_id,'') != '' 
                    )t
                    WHERE m.id = t.id
        """ 
        self._cr.execute(strSQL)
        _logger.debug('Updated Phone and First Names')


    def upload_missing_records(self):
        row_nums = 0
        recs = []
        for rec in self.missing_recon_ids:
            row_nums = row_nums + 1
            _bill_ref_number = str(rec.bill_ref_number).upper()
       
            vals = {
                    'paybill_number': rec.paybill_number,
                    'company_id':rec.company_id.id,
                    'transaction_type': rec.transaction_type ,
                    'trans_id': rec.trans_id,
                    'trans_time': rec.transaction_date_time.strftime('%Y%m%d%H%M%S'),
                    'transaction_date_time': rec.transaction_date_time,
                    'trans_amount': rec.trans_amount,
                    'bill_ref_number': rec.bill_ref_number,
                    'payer_phone_number': rec.payer_phone_number,
                    'payer_name' : rec.payer_name,
                    'comments': 'RECONIMPORT: ' + str(rec.trans_details),
                    'amount_residual': rec.trans_amount,
                    'amount_applied':0,
                    'active':True,
                    # 'company_id': ,#TODO
                    # 'partner_id': ,#TODO
                    # 'toilet_id': _found_toilet_id,
                    # 'auto_matched': _auto_matched,
                    # 'deposit_invoice_id':_found_deposit_invoice
            }
            # print (str(vals) + str('\n'))
            recs.append(vals)
        
        if recs:
            res = self.env['mpesa.base'].sudo().create(recs)


class MPesaReconView(models.AbstractModel):
    _name = "mpesa.reconcile.view"
    _description = 'MPesa Reconciliations View'
    _auto = False

    recon_wizard_id = fields.Many2one('mpesa.reconcile.import', string="Recon Wizard ID")
    paybill_number = fields.Char(string="Paybill Number")
    company_id = fields.Many2one('res.company', string="Company")
    reference = fields.Integer(string='Row Number')
    trans_id = fields.Char(string='Record Name')
    transaction_type = fields.Char(string='Transaction Type')
    transaction_date_time = fields.Datetime(string="Transaction Date")
    trans_amount = fields.Integer(string='Transaction Amount')
    bill_ref_number = fields.Char(string='Bill Ref Number')
    payer_name = fields.Char(string='Payer Name')
    payer_phone_number = fields.Char(string='Phone Number')
    trans_details = fields.Char(string='Transaction Details') 
    

    # def init(self):
    #     """ MPesa Reconcile View """
    #     tools.drop_view_if_exists(self.env.cr, self._table)
    #     strSQL = """ CREATE or REPLACE VIEW mpesa_reconcile_view AS (
    #         SELECT id, recon_wizard_id, paybill_number, company_id,reference, trans_id, transaction_type, transaction_date_time,
    #         trans_amount, bill_ref_number, payer_name,payer_phone_number,trans_details
    #         FROM mpesa_reconcile 
    #         WHERE trans_id NOT IN 
    #         (
    #             SELECT trans_id 
    #             FROM 
    #             (
    #                 SELECT trans_id, transaction_date_time at time zone 'UTC' transaction_date_time
    #                 FROM mpesa_base
    #                 WHERE paybill_number = '%s'
    #             ) t
    #             WHERE transaction_date_time::date BETWEEN 
    #             (SELECT MIN(transaction_date_time::date) FROM mpesa_reconcile WHERE paybill_number = '%s') AND 
    #             (SELECT MAX(transaction_date_time::date) FROM mpesa_reconcile WHERE paybill_number = '%s')
    #         )
    #         ORDER BY reference
    #     )""" % (self.paybill_number,self.paybill_number,self.paybill_number)
        
    #     print(strSQL)
    #     self.env.cr.execute(strSQL)
    def abd(self):
        strSQL = """SELECT p.id parent_id, p.name parent_name, c.id child_id, c.name child_name
            FROM res_partner c 
            INNER JOIN res_partner p 
            ON p.id = c.parent_id
            where c.company_id = 2 and c.parent_id is not null AND p.create_date::date = '2022-08-26'
            LIMIT 10        
        """
        print(strSQL)
        self.env.cr.execute(strSQL)
        query_res = self._cr.dictfetchall()
        
        vals = []
        if query_res:
            for rec in query_res:
                child_rec = self.env['res.partner'].search((['id','=',rec.get('child_id')]))
                if child_rec:
                    child_rec.update({'parent_id':None})
                    print('Updated Parent Record',child_rec.name)
