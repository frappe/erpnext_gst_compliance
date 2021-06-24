import re
import os
import io
import base64
import frappe

from frappe import _
from json import dumps
from pyqrcode import create as qrcreate
from erpnext_gst_compliance.utils import log_exception
from frappe.integrations.utils import make_post_request, make_get_request
from frappe.utils.data import add_to_date, time_diff_in_seconds, now_datetime

class AdequareConnector:
	def __init__(self, gstin):

		self.gstin = gstin
		self.settings = frappe.get_cached_doc("Adequare Settings")
		self.credentials = self.get_user_credentials()
		self.host = self.get_host_url()
		self.endpoints = self.get_endpoints()

		self.validate()

	def get_user_credentials(self):
		return next(filter(lambda row: row.gstin == self.gstin, self.settings.credentials), frappe._dict())

	def get_host_url(self):
		if self.settings.sandbox_mode:
			return "https://gsp.adaequare.com/test"
		else:
			return "https://gsp.adaequare.com"

	def get_endpoints(self):
		return frappe._dict({
			"authenticate": 'https://gsp.adaequare.com/gsp/authenticate?grant_type=token',
			"generate_irn": self.host + '/enriched/ei/api/invoice',
			"cancel_irn": self.host + '/enriched/ei/api/invoice/cancel',
			"irn_details": self.host + '/enriched/ei/api/invoice/irn',
			"gstin_details": self.host + '/enriched/ei/api/master/gstin',
			"cancel_ewaybill": self.host + '/enriched/ewb/ewayapi?action=CANEWB',
			"generate_ewaybill": self.host + '/enriched/ei/api/ewaybill',
		})

	def validate(self):
		if not self.settings.enabled:
			frappe.throw(_("Adequare Settings is not enabled. Please configure Adequare Settings and try again."))

	@log_exception
	def make_request(self, req_type, url, headers, payload):
		if req_type == 'post':
			response = make_post_request(url, headers=headers, data=payload)
		else:
			response = make_get_request(url, headers=headers, data=payload)
			
		self.log_einvoice_request(url, headers, payload, response)
		
		return response

	def log_einvoice_request(self, url, headers, payload, response):
		headers.update({ 'password': self.credentials.password })
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
	def fetch_auth_token(self):
		headers = {
			'gspappid': frappe.conf.einvoice_client_id,
			'gspappsecret': frappe.conf.einvoice_client_secret
		}
		url = self.endpoints.authenticate
		res = self.make_request('post', url, headers, None)
		self.settings.auth_token = "{} {}".format(res.get('token_type'), res.get('access_token'))
		self.settings.token_expiry = add_to_date(None, seconds=res.get('expires_in'))
		self.settings.save(ignore_permissions=True)
		self.settings.reload()
		frappe.db.commit()

	@log_exception
	def get_auth_token(self):
		if time_diff_in_seconds(self.settings.token_expiry, now_datetime()) < 150.0:
			self.fetch_auth_token()

		return self.settings.auth_token

	@log_exception
	def get_headers(self):
		return {
			'content-type': 'application/json',
			'user_name': self.credentials.username,
			'password': self.credentials.get_password(),
			'gstin': self.credentials.gstin,
			'authorization': self.get_auth_token(),
			'requestid': str(base64.b64encode(os.urandom(18))),
		}

	@log_exception
	def make_irn_request(self):
		headers = self.get_headers()
		url = self.endpoints.generate_irn

		einvoice_json = self.einvoice.get_einvoice_json()
		payload = dumps(einvoice_json, indent=4)

		response = self.make_request('post', url, headers, payload)

		if response.get('success'):
			govt_response = response.get('result')
			self.handle_successful_irn_generation(govt_response)
		elif '2150' in response.get('message'):
			govt_response = response.get('result')
			self.handle_irn_already_generated(govt_response)
		else:
			errors = response.get('message')
			errors = self.sanitize_error_message(errors)
			return False, errors

		return True, []

	@staticmethod
	def generate_irn(einvoice):
		gstin = einvoice.seller_gstin
		connector = AdequareConnector(gstin)
		connector.einvoice = einvoice
		success, errors = connector.make_irn_request()

		return success, errors

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

	def handle_irn_already_generated(self, response):
		# IRN already generated but not updated in invoice
		# Extract the IRN from the response description and fetch irn details
		irn = response[0].get('Desc').get('Irn')
		success, irn_details = self.make_get_irn_details_request(irn)
		if success:
			self.handle_successful_irn_generation(irn_details)

	def sanitize_error_message(self, message):
		'''
			On validation errors, response message looks something like this:
			message = '2174 : For inter-state transaction, CGST and SGST amounts are not applicable; only IGST amount is applicable,
						3095 : Supplier GSTIN is inactive'
			we search for string between ':' to extract the error messages
			errors = [
				': For inter-state transaction, CGST and SGST amounts are not applicable; only IGST amount is applicable, 3095 ',
				': Test'
			]
			then we trim down the message by looping over errors
		'''
		if not message:
			return []

		if not ' : ' in message:
			return [message]

		errors = re.findall(' : [^:]+', message)
		for idx, e in enumerate(errors):
			# remove colons
			errors[idx] = errors[idx].replace(':', '').strip()
			# if not last
			if idx != len(errors) - 1:
				# remove last 7 chars eg: ', 3095 '
				errors[idx] = errors[idx][:-6]

		return errors

	@log_exception
	def make_get_irn_details_request(self, irn):
		headers = self.get_headers()
		url = self.endpoints.irn_details

		params = '?irn={irn}'.format(irn=irn)
		response = self.make_request('get', url + params, headers, None)

		if response.get('success'):
			return True, response.get('result')
		else:
			errors = response.get('message')
			errors = self.sanitize_error_message(errors)
			return False, errors

