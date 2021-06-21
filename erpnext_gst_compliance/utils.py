import six
import sys
import json
import frappe
import traceback
from frappe import _

class HandledException(Exception): pass

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
