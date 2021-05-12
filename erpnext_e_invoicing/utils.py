import six
import sys
import json
import frappe
import traceback
from frappe import _
from frappe.utils import cint, getdate

class HandledException(Exception): pass

@frappe.whitelist()
def validate_einvoice_eligibility(doc):
	if isinstance(doc, six.string_types):
		doc = json.loads(doc)

	invalid_doctype = doc.get('doctype') != 'Sales Invoice'
	if invalid_doctype:
		return False

	service_provider = frappe.db.get_single_value('E Invoicing Settings', 'service_provider')
	if not service_provider:
		return False
	
	einvoicing_enabled = cint(frappe.db.get_single_value(service_provider, 'enabled'))
	if not einvoicing_enabled:
		return False

	einvoicing_eligible_from = '2021-04-01'
	if getdate(doc.get('posting_date')) < getdate(einvoicing_eligible_from):
		return False

	# TODO - add company check
	invalid_supply_type = doc.get('gst_category') not in ['Registered Regular', 'SEZ', 'Overseas', 'Deemed Export']
	inter_company_transaction = doc.get('billing_address_gstin') == doc.get('company_gstin')
	no_taxes_applied = not doc.get('taxes')

	if invalid_supply_type or inter_company_transaction or no_taxes_applied:
		return False

	return True

def log_exception(fn):
	'''Decorator to catch & log exceptions'''

	def wrapper(*args, **kwargs):
		return_value = None
		try:
			return_value = fn(*args, **kwargs)
		except HandledException:
			raise
		except Exception:
			log_error()
			raise HandledException

		return return_value

	return wrapper

def log_error():
	frappe.db.rollback()
	seperator = "--" * 50
	err_tb = traceback.format_exc()
	err_msg = str(sys.exc_info()[1])
	# data = json.dumps(data, indent=4)
	
	message = "\n".join([
		"Error: " + err_msg, seperator,
		# "Data:", data, seperator,
		"Exception:", err_tb
	])
	frappe.log_error(
		title=_('Handled Exception'), 
		message=message
	)
	frappe.db.commit()

def safe_load_json(message):
	JSONDecodeError = ValueError if six.PY2 else json.JSONDecodeError

	try:
		json_message = json.loads(message)
	except JSONDecodeError:
		json_message = message

	return json_message
