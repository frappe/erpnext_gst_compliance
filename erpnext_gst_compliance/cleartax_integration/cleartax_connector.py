import frappe

from frappe import _
from json import dumps
from erpnext_e_invoicing.utils import log_exception
from frappe.integrations.utils import make_post_request, make_get_request, make_put_request
from erpnext_e_invoicing.erpnext_e_invoicing.doctype.e_invoice.e_invoice import create_einvoice

class CleartaxConnector:
	def __init__(self, gstin):

		self.gstin = gstin
		self.settings = frappe.get_cached_doc("Cleartax Settings")
		self.business = self.get_business_settings()
		self.auth_token = self.settings.auth_token
		self.host = self.get_host_url()
		self.endpoints = self.get_endpoints()

		self.validate()

	def get_business_settings(self):
		return next(
			filter(lambda row: row.gstin == self.gstin, self.settings.credentials),
			frappe._dict({}),
		)

	def get_host_url(self):
		if self.settings.sandbox_mode:
			return "https://einvoicing.internal.cleartax.co"
		else:
			return "https://api-einv.cleartax.in"

	def get_endpoints(self):
		base_url = self.host + "/v2/eInvoice"
		return frappe._dict({
			"generate_irn": base_url + "/generate",
			"cancel_irn": base_url + "/cancel",
			"generate_ewaybill": base_url + "/ewaybill",
			"cancel_ewaybill": base_url + "/ewaybill/cancel"
		})

	def validate(self):
		if not self.settings.enabled:
			frappe.throw(_("Cleartax Settings is not enabled. Please configure Cleartax Settings and try again."))

		if not self.business.owner_id:
			frappe.throw(
				_("Cannot find Owner ID for GSTIN {}. Please add cleartax credentials for mentioned GSTIN in Cleartax Settings. ")
					.format(self.gstin))

	@log_exception
	def get_headers(self):
		return frappe._dict({
			"x-cleartax-auth-token": self.settings.get_password('auth_token'),
			"x-cleartax-product": "EInvoice",
			"Content-Type": "application/json",
			"owner_id": self.business.get_password('owner_id'),
			"gstin": self.gstin
		})

	def log_einvoice_request(self, url, headers, payload, response):
		headers.update({
			"x-cleartax-auth-token": self.auth_token,
			"owner_id": self.business.owner_id
		})
		request_log = frappe.get_doc({
			"doctype": "E Invoice Request Log",
			"user": frappe.session.user,
			"reference_invoice": None, # TODO: set invoice reference?
			"url": url,
			"headers": dumps(headers, indent=4) if headers else None,
			"data": dumps(payload, indent=4) if isinstance(payload, dict) else payload,
			"response": dumps(response, indent=4) if response else None
		})
		request_log.save(ignore_permissions=True)
		frappe.db.commit()

	@log_exception
	def make_request(self, req_type, url, headers, payload):
		if req_type == 'post':
			response = make_post_request(url, headers=headers, data=payload)
		elif req_type == 'put':
			response = make_put_request(url, headers=headers, data=payload)
		else:
			response = make_get_request(url, headers=headers, data=payload)
			
		self.log_einvoice_request(url, headers, payload, response)
		
		return response

	@log_exception
	def generate_irn(self, invoice_number):
		headers = self.get_headers()
		url = self.endpoints.generate_irn

		einvoice = create_einvoice(invoice_number)
		einvoice_json = einvoice.get_einvoice_json()

		payload = [{"transaction": einvoice_json}]
		payload = dumps(payload, indent=4)

		response = self.make_request('put', url, headers, payload)
