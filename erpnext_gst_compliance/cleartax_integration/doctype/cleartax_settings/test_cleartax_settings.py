# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
from erpnext_gst_compliance.cleartax_integration.cleartax_connector import CleartaxConnector
from erpnext_gst_compliance.erpnext_gst_compliance.doctype.e_invoice.test_e_invoice import make_e_invoice

class TestCleartaxSettings(unittest.TestCase):
	
	def test_incorrect_company_gstin(self):
		cleartax_settings = frappe.get_doc('Cleartax Settings')
		cleartax_settings.enabled = 1

		cleartax_settings.append('credentials', {
			'company': '_Test Company',
			'gstin': '27AAFCD5862R013',
			'owner_id': 'test_owner_id'
		})

		self.assertRaises(frappe.ValidationError, cleartax_settings.save)

class TestCleartaxConnector(unittest.TestCase):
	def setUp(self):
		cleartax_settings = frappe.get_single('Cleartax Settings')
		cleartax_settings.enabled = 1
		cleartax_settings.credentials = []
		cleartax_settings.append('credentials', {
			'company': '_Test Company',
			'gstin': '27AAECE4835E1ZR',
			'owner_id': 'test_owner_id'
		})
		cleartax_settings.flags.ignore_validate = True
		cleartax_settings.save()

		einvoice, _ = make_e_invoice()
		self.connector = CleartaxConnector('27AAECE4835E1ZR')
		self.connector.einvoice = einvoice

		self.valid_irn_response = [{
			"document_status": "IRN_GENERATED",
			"govt_response": {
				"Success": "Y",
				"AckNo": 112110085331107,
				"AckDt": "2021-06-19 23:17:00",
				"Irn": "47d1353009acd3db7c999b174b1c68f52e382f88a497921be49be31f9769b017",
				"SignedInvoice": "eyJhbGciOiJSUzI1NiIsImtpZCI6IkVEQzU3REUxMzU4QjMwMEJBOUY3OTM0MEE2Njk2ODMxRjNDODUwNDciLCJ0eXAiOiJKV1QiLCJ4NXQiOiI3Y1Y5NFRXTE1BdXA5NU5BcG1sb01mUElVRWMifQ.eyJkYXRhIjoie1wiQWNrTm9cIjoxMTIxMTAwODUzMzExMDcsXCJBY2tEdFwiOlwiMjAyMS0wNi0xOSAyMzoxNzowMFwiLFwiSXJuXCI6XCI0N2QxMzUzMDA5YWNkM2RiN2M5OTliMTc0YjFjNjhmNTJlMzgyZjg4YTQ5NzkyMWJlNDliZTMxZjk3NjliMDE3XCIsXCJWZXJzaW9uXCI6XCIxLjFcIixcIlRyYW5EdGxzXCI6e1wiVGF4U2NoXCI6XCJHU1RcIixcIlN1cFR5cFwiOlwiQjJCXCIsXCJSZWdSZXZcIjpcIk5cIixcIklnc3RPbkludHJhXCI6XCJOXCJ9LFwiRG9jRHRsc1wiOntcIlR5cFwiOlwiSU5WXCIsXCJOb1wiOlwiU0lOVi0yMS0wMDAwN1wiLFwiRHRcIjpcIjE5LzA2LzIwMjFcIn0sXCJTZWxsZXJEdGxzXCI6e1wiR3N0aW5cIjpcIjI5QUFGQ0Q1ODYyUjAwMFwiLFwiTGdsTm1cIjpcIlVuaWNvIFBsYXN0aWNzIFB2dC4gTHRkLlwiLFwiQWRkcjFcIjpcIkFrc2h5YSBOYWdhciAxc3QgQmxvY2sgMXN0IENyb3NzLCBSYW1tdXJ0aHkgbmFnYXJcIixcIkxvY1wiOlwiQmFuZ2Fsb3JlXCIsXCJQaW5cIjo1NjAwMTYsXCJTdGNkXCI6XCIyOVwifSxcIkJ1eWVyRHRsc1wiOntcIkdzdGluXCI6XCIyN0FBQkNVOTYwM1IxWk5cIixcIkxnbE5tXCI6XCJBdmFyeWEgUmV0YWlsIFB2dC4gTHRkLlwiLFwiUG9zXCI6XCIyN1wiLFwiQWRkcjFcIjpcIkJhamFqIEJoYXZhbiwgR3JkIEZsb29yLCBOYXJpbWFuIFBvaW50IFJvYWQsIE5hcmltYW4gUG9pbnRcIixcIkxvY1wiOlwiTXVtYmFpXCIsXCJQaW5cIjo0MDAwMjEsXCJTdGNkXCI6XCIyN1wifSxcIkl0ZW1MaXN0XCI6W3tcIkl0ZW1Ob1wiOjAsXCJTbE5vXCI6XCIxXCIsXCJJc1NlcnZjXCI6XCJOXCIsXCJQcmREZXNjXCI6XCJBcHBsZSBFYXJwb2RzXCIsXCJIc25DZFwiOlwiODUxODMwMDBcIixcIlF0eVwiOjEuMCxcIlVuaXRcIjpcIk5PU1wiLFwiVW5pdFByaWNlXCI6NjAwMC4wLFwiVG90QW10XCI6NjAwMC4wMCxcIkRpc2NvdW50XCI6MC4wMCxcIkFzc0FtdFwiOjYwMDAuMDAsXCJHc3RSdFwiOjE4LjAwLFwiSWdzdEFtdFwiOjEwODAuMDAsXCJDZ3N0QW10XCI6MC4wMCxcIlNnc3RBbXRcIjowLjAwLFwiQ2VzUnRcIjowLjAwLFwiQ2VzQW10XCI6MC4wMCxcIkNlc05vbkFkdmxBbXRcIjowLjAwLFwiT3RoQ2hyZ1wiOjAuMDAsXCJUb3RJdGVtVmFsXCI6NzA4MC4wMH1dLFwiVmFsRHRsc1wiOntcIkFzc1ZhbFwiOjYwMDAuMDAsXCJDZ3N0VmFsXCI6MC4wMCxcIlNnc3RWYWxcIjowLjAwLFwiSWdzdFZhbFwiOjEwODAuMDAsXCJDZXNWYWxcIjowLjAwLFwiRGlzY291bnRcIjowLjAwLFwiT3RoQ2hyZ1wiOjAuMDAsXCJSbmRPZmZBbXRcIjowLjAwLFwiVG90SW52VmFsXCI6NzA4MC4wMCxcIlRvdEludlZhbEZjXCI6NzA4MC4wMH19IiwiaXNzIjoiTklDIn0.NZrxxau7RQyky2kq9HsfWGcQ35OWkL4XYMKk_FuHbsUa-q-PL-FeY6YuSfcLy6EqTRDvPexvfTsN_tQeNzzocvR3G0rVsEHHnB-yoZuWn66UDWXokkiPFR3KQf0tBYWCnummmfpjIiSNWlf0Ib-DJ3SprxmpF0cQ_RL2jJKcEUfVDy2G7y7MQZ2TAPGaIy3pdaZDVZe3zKeG6fWb6oJtFtJk9lV7mzQrpCnHO6BA8ChoLwKR_6RwJwwCAdF8FYKV9obYDTcjzyxnBBc2Z2sgc8Q29MBgWpoHo6MjF3axR025_nAvxK540mi45JzNJsNS6oSsaKunQtDKFfh90TDqOg",
				"SignedQRCode": "eyJhbGciOiJSUzI1NiIsImtpZCI6IkVEQzU3REUxMzU4QjMwMEJBOUY3OTM0MEE2Njk2ODMxRjNDODUwNDciLCJ0eXAiOiJKV1QiLCJ4NXQiOiI3Y1Y5NFRXTE1BdXA5NU5BcG1sb01mUElVRWMifQ.eyJkYXRhIjoie1wiU2VsbGVyR3N0aW5cIjpcIjI5QUFGQ0Q1ODYyUjAwMFwiLFwiQnV5ZXJHc3RpblwiOlwiMjdBQUJDVTk2MDNSMVpOXCIsXCJEb2NOb1wiOlwiU0lOVi0yMS0wMDAwN1wiLFwiRG9jVHlwXCI6XCJJTlZcIixcIkRvY0R0XCI6XCIxOS8wNi8yMDIxXCIsXCJUb3RJbnZWYWxcIjo3MDgwLjAwLFwiSXRlbUNudFwiOjEsXCJNYWluSHNuQ29kZVwiOlwiODUxODMwMDBcIixcIklyblwiOlwiNDdkMTM1MzAwOWFjZDNkYjdjOTk5YjE3NGIxYzY4ZjUyZTM4MmY4OGE0OTc5MjFiZTQ5YmUzMWY5NzY5YjAxN1wiLFwiSXJuRHRcIjpcIjIwMjEtMDYtMTkgMjM6MTc6MDBcIn0iLCJpc3MiOiJOSUMifQ.BixNn3wWO7SGYdKhqNWL_djEAVSDeH3haHseJ_vEF2y-XOcBmoC6tbTk83xdiLlwORwlnw6qxS5ClarT5xTAPLWNqrW2E-buydqXdNTQKkZgYe0DCSj_1ItEYMfZ_9zvglHYKPBz_kmG_CiDODcpcbIEcWE35TrCLJCoezb4WhSrT9VbaWRMo1zyHWu9vbKUXGcX27zlWnaCQbG_5W3_lsgz9g2fx6RME7u4otMvHyEBpPM6nAdeSCh_hx7X24U0fejwNMAGW2Y_qoqk0UcyT3THVaeWxcB4R5USczSD3KjFBCN-T6mFV5iprXrMewnWQOeu1QT6cxMUfaUkk1LHsw",
				"Status": "ACT"
			},
			"gstin": "27AAECE4835E1ZR",
			"owner_id": None,
		}]

		self.invalid_irn_response = [{
			"document_status": "IRN_GENERATION_FAILED",
			"govt_response": {
				"Success": "N",
				"ErrorDetails": [
					{
						"error_code": "107",
						"error_message": "lineItems[0].gstRate : Invalid GST Tax rate. Please correct the Tax Rate Values and try again",
						"error_source": "CLEARTAX"
					},
					{
						"error_code": "107",
						"error_message": "lineItems[0].igstAmount : Invalid value of Tax Amount, provide either IGST or both SGST and CGST",
						"error_source": "CLEARTAX"
					}
				]
			},
			"gstin": "27AAECE4835E1ZR",
			"owner_id": None,
		}]

		self.valid_irn_cancel_response = [{
			"document_status": "IRN_CANCELLED",
			"govt_response": {
				"Success": "Y",
				"Irn": "736499fdad251b128f6ff55f7518600f7361335f32d972915e3e0589225697d5",
				"CancelDate": "2021-06-19 22:10:00"
			},
			"gstin": "29AAFCD5862R000",
			"owner_id": None
		}]
	
	def test_irn_generation(self):
		# with successful response
		response = self.valid_irn_response
		response = self.connector.sanitize_response(response)
		self.connector.handle_successful_irn_generation(response)
		self.assertTrue(response.get('Success'))
		self.assertEqual(self.connector.einvoice.irn, response.get('Irn'))
		self.assertEqual(self.connector.einvoice.ack_no, response.get('AckNo'))
		self.assertEqual(self.connector.einvoice.ack_date, response.get('AckDt'))
		self.assertEqual(self.connector.einvoice.status, 'IRN Generated')

		# with error response
		response = self.invalid_irn_response
		response = self.connector.sanitize_response(response)
		errors = response.get('Errors')
		self.assertFalse(response.get('Success'))
		self.assertEqual(len(errors), 2)
	
	def test_irn_cancellation(self):
		# with successful response
		response = self.valid_irn_cancel_response
		response = self.connector.sanitize_response(response)
		self.connector.handle_successful_irn_cancellation(response)
		self.assertTrue(response.get('Success'))
		self.assertEqual(self.connector.einvoice.irn_cancelled, 1)
		self.assertEqual(self.connector.einvoice.irn_cancel_date, response.get('CancelDate'))
		self.assertEqual(self.connector.einvoice.status, 'IRN Cancelled')

	def tearDown(self):
		cleartax_settings = frappe.get_single('Cleartax Settings')
		cleartax_settings.enabled = 0
		cleartax_settings.auth_token = None
		cleartax_settings.token_expiry = None
		cleartax_settings.flags.ignore_validate = True
		cleartax_settings.save()