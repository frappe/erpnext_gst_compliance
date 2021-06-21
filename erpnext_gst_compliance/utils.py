import sys
import json
import frappe
import traceback
from frappe import _

class HandledException(frappe.ValidationError): pass

def log_exception(fn):
	'''Decorator to catch & log exceptions'''

	def wrapper(*args, **kwargs):
		return_value = None
		try:
			return_value = fn(*args, **kwargs)
		except HandledException:
			# exception has been logged, so just raise a proper error message
			frappe.clear_messages()
			show_request_failed_error()
		except Exception:
			log_error()
			raise HandledException

		return return_value

	return wrapper

def show_request_failed_error():
	message = _('There was an error while making the request.') + ' '
	message += _('Please try once again and if the issue persists, please contact ERPNext Support.')
	frappe.throw(message, title=_('Request Failed'), exc=HandledException)

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
		title=_('E-Invoicing Exception'),
		message=message
	)
	frappe.db.commit()

def safe_load_json(message):
	try:
		json_message = json.loads(message)
	except Exception:
		json_message = message

	return json_message
