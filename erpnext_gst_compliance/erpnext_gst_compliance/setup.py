import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def setup():
    setup_custom_fields()

def setup_custom_fields():
	custom_fields = {
		'Sales Invoice': [
			dict(fieldname='einvoice_section', label='E-Invoice Details', fieldtype='Section Break', insert_after='amended_from',
				print_hide=1, depends_on='e_invoice', collapsible=1, collapsible_depends_on='e_invoice'),
		
			dict(fieldname='e_invoice', label='E-Invoice', fieldtype='Link', read_only=1, insert_after='einvoice_section',
				options='E Invoice', no_copy=1, print_hide=1, depends_on='e_invoice'),
			
			dict(fieldname='irn', label='IRN', fieldtype='Data', read_only=1, insert_after='e_invoice', no_copy=1, print_hide=1,
				depends_on='eval: doc.e_invoice_status != "IRN Cancelled"', fetch_from='e_invoice.irn'),
			
			dict(fieldname='ack_no', label='Ack. No.', fieldtype='Data', read_only=1, insert_after='irn', no_copy=1,
				depends_on='eval: doc.e_invoice_status != "IRN Cancelled"', fetch_from='e_invoice.ack_no', print_hide=1),

			dict(fieldname='irn_cancel_date', label='IRN Cancelled On', fieldtype='Data', read_only=1, insert_after='ack_no', 
				depends_on='eval: doc.e_invoice_status == "IRN Cancelled"', fetch_from='e_invoice.irn_cancel_date', no_copy=1, print_hide=1),
			
			dict(fieldname='col_break_1', label='', fieldtype='Column Break', insert_after='irn_cancel_date',
				print_hide=1, read_only=1),

			dict(fieldname='e_invoice_status', label='E-Invoice Status', fieldtype='Data', read_only=1, no_copy=1,
				insert_after='col_break_1', print_hide=1, depends_on='e_invoice', fetch_from='e_invoice.status'),

			dict(fieldname='ack_date', label='Ack. Date', fieldtype='Data', read_only=1, insert_after='e_invoice_status',
				depends_on='eval: doc.e_invoice_status != "IRN Cancelled"', fetch_from='e_invoice.ack_date',  no_copy=1, print_hide=1),

			dict(fieldname='qrcode_image', label='QRCode', fieldtype='Attach Image', hidden=1, insert_after='ack_date',
				fetch_from='e_invoice.qrcode_path', no_copy=1, print_hide=1, read_only=1)
		]
	}

	print('Creating Custom Fields for E-Invoicing...')
	create_custom_fields(custom_fields, update=True)