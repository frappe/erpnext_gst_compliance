import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def setup():
    setup_custom_fields()

def setup_custom_fields():
	company = frappe.get_all('Company', filters = {'country': 'India'})
	if not company:
		return
		
	custom_fields = {
		'Sales Invoice': [
			dict(fieldname='e_invoice_section', label='E-Invoice Details', fieldtype='Section Break', insert_after='amended_from',
				print_hide=1, depends_on='e_invoice', collapsible=1, collapsible_depends_on='e_invoice'),
		
			dict(fieldname='e_invoice', label='E-Invoice', fieldtype='Link', read_only=1, insert_after='e_invoice_section',
				options='E Invoice', no_copy=1, print_hide=1, depends_on='e_invoice'),
			
			dict(fieldname='col_break_1', label='', fieldtype='Column Break', insert_after='e_invoice',
				print_hide=1, read_only=1),

			dict(fieldname='e_invoice_status', label='E-Invoice Status', fieldtype='Data', read_only=1, no_copy=1,
				insert_after='col_break_1', print_hide=1, depends_on='e_invoice', fetch_from='e_invoice.status'),
		]
	}

	create_custom_fields(custom_fields, update=True)