import os
import io
import frappe

from frappe import _
from json import dumps
from pyqrcode import create as qrcreate
from erpnext_gst_compliance.utils import log_exception
from frappe.integrations.utils import make_post_request, make_get_request, make_put_request

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
			"reference_invoice": self.einvoice.name,
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
	def make_irn_request(self):
		headers = self.get_headers()
		url = self.endpoints.generate_irn

		einvoice_json = self.einvoice.get_einvoice_json()

		payload = [{"transaction": einvoice_json}]
		payload = dumps(payload, indent=4)

		response = self.make_request('put', url, headers, payload)
		# Sample Response -> https://docs.cleartax.in/cleartax-for-developers/e-invoicing-api/e-invoicing-api-reference/cleartax-e-invoicing-apis-xml-schema#sample-response

		response = self.sanitize_response(response)
		if response.get('Success'):
			self.handle_successful_irn_generation(response)

		return response

	@staticmethod
	def generate_irn(einvoice):
		business_gstin = einvoice.seller_gstin
		connector = CleartaxConnector(business_gstin)
		connector.einvoice = einvoice
		response = connector.make_irn_request()
		success, errors = response.get('Success'), response.get('Errors')

		return success, errors

	def sanitize_response(self, response):
		sanitized_response = []
		for entry in response:
			govt_response = frappe._dict(entry.get('govt_response', {}))
			success = govt_response.get('Success', "N")

			if success == "Y":
				# return irn & other info
				govt_response.update({'Success': True})
				sanitized_response.append(govt_response)
			else:
				# return error message list
				error_details = govt_response.get('ErrorDetails', [])
				error_list = []

				for d in error_details:
					if d.get('error_source') == 'CLEARTAX':
						# cleartax gives back the exact key that causes the error
						# error_message = "sellerDetails.pinCode : <actual error message>"
						d['error_message'] = d['error_message'].split(' : ')[-1]
					error_list.append(d.get('error_message'))

				sanitized_response.append({
					'Success': False,
					'Errors': error_list
				})

		return sanitized_response[0] if len(sanitized_response) == 1 else sanitized_response

	def handle_successful_irn_generation(self, response):
		status = 'IRN Generated'
		irn = response.get('Irn')
		ack_no = response.get('AckNo')
		ack_date = response.get('AckDt')
		ewaybill = response.get('EwbNo')
		ewaybill_validity = response.get('EwbValidTill')
		qrcode = self.generate_qrcode(response.get('SignedQRCode'))

		self.einvoice.update({
			'irn': irn,
			'status': status,
			'ack_no': ack_no,
			'ack_date': ack_date,
			'ewaybill': ewaybill,
			'qrcode_path': qrcode,
			'ewaybill_validity': ewaybill_validity
		})
		self.einvoice.flags.ignore_permissions = 1
		self.einvoice.submit()

	def generate_qrcode(self, signed_qrcode):
		doctype = self.einvoice.doctype
		docname = self.einvoice.name
		filename = '{} - QRCode.png'.format(docname).replace(os.path.sep, "__")

		qr_image = io.BytesIO()
		url = qrcreate(signed_qrcode, error='L')
		url.png(qr_image, scale=2, quiet_zone=1)
		_file = frappe.get_doc({
			'doctype': 'File',
			'file_name': filename,
			'attached_to_doctype': doctype,
			'attached_to_name': docname,
			'attached_to_field': 'qrcode_path',
			'is_private': 1,
			'content': qr_image.getvalue()
		})
		_file.save()
		return _file.file_url

	@log_exception
	def make_cancel_irn_request(self, reason, remark):
		headers = self.get_headers()
		url = self.endpoints.cancel_irn

		irn = self.einvoice.irn

		payload = [{'irn': irn, 'CnlRsn': reason, 'CnlRem': remark}]
		payload = dumps(payload, indent=4)

		response = self.make_request('put', url, headers, payload)
		# Sample Response -> https://docs.cleartax.in/cleartax-for-developers/e-invoicing-api/e-invoicing-api-reference/cleartax-e-invoicing-apis-xml-schema#sample-response-1

		response = self.sanitize_response(response)
		if response.get('Success'):
			self.handle_successful_irn_cancellation(response)

		return response

	def handle_successful_irn_cancellation(self, response):
		self.einvoice.irn_cancelled = 1
		self.einvoice.irn_cancel_date = response.get('CancelDate')
		self.einvoice.status = 'IRN Cancelled'
		self.einvoice.flags.ignore_validate_update_after_submit = 1
		self.einvoice.flags.ignore_permissions = 1
		self.einvoice.save()

	@staticmethod
	def cancel_irn(einvoice, reason, remark):
		business_gstin = einvoice.seller_gstin
		connector = CleartaxConnector(business_gstin)
		connector.einvoice = einvoice
		response = connector.make_cancel_irn_request(reason, remark)
		success, errors = response.get('Success'), response.get('Errors')

		return success, errors

	@log_exception
	def make_eway_bill_request(self):
		headers = self.get_headers()
		url = self.endpoints.generate_ewaybill

		eway_bill_json = self.einvoice.get_eway_bill_json()

		payload = [eway_bill_json]
		payload = dumps(payload, indent=4)

		response = self.make_request('post', url, headers, payload)
		# Sample Response -> https://docs.cleartax.in/cleartax-for-developers/e-invoicing-api/e-invoicing-api-reference/cleartax-e-invoicing-apis-xml-schema#sample-response-3

		response = self.sanitize_response(response)
		if response.get('Success'):
			self.handle_successful_ewaybill_generation(response)

		return response

	def handle_successful_ewaybill_generation(self, response):
		self.einvoice.ewaybill = response.get('EwbNo')
		self.einvoice.ewaybill_validity = response.get('EwbValidTill')
		self.einvoice.status = 'E-Way Bill Generated'
		self.einvoice.flags.ignore_validate_update_after_submit = 1
		self.einvoice.flags.ignore_permissions = 1
		self.einvoice.save()

	@staticmethod
	def generate_eway_bill(einvoice):
		business_gstin = einvoice.seller_gstin
		connector = CleartaxConnector(business_gstin)
		connector.einvoice = einvoice
		response = connector.make_eway_bill_request()
		success, errors = response.get('Success'), response.get('Errors')

		return success, errors