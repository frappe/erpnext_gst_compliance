import frappe
from frappe import _

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

	def get_headers(self):
		return frappe._dict({
			"x-cleartax-auth-token": self.auth_token
			"x-cleartax-product": "EInvoice"
			"Content-Type": "application/json"
			"owner_id": self.business.owner_id
			"gstin": self.gstin
		})