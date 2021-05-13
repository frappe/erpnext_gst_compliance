import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
	company = frappe.get_all('Company', filters = {'country': 'India'})
	if not company:
		return
		
	custom_fields = {
		'Sales Invoice': [
			dict(fieldname='e_invoice_section', label='E-Invoice Details', fieldtype='Section Break', insert_after='amended_from',
				print_hide=1, depends_on='e_invoice', collapsible=1, collapsible_depends_on='e_invoice'),
		
			dict(fieldname='e_invoice', label='E-Invoice', fieldtype='Link', read_only=1, insert_after='einvoice_section',
				options='E Invoice', no_copy=1, print_hide=1, depends_on='e_invoice'),

			dict(fieldname='e_invoice_status', label='E-Invoice Status', fieldtype='Data', read_only=1, insert_after='e_invoice',
				no_copy=1, print_hide=1, depends_on='e_invoice'),
		]
	}

	create_custom_fields(custom_fields, update=True)

