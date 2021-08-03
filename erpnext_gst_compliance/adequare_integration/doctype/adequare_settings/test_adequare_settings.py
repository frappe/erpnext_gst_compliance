# Copyright (c) 2021, Frappe Technologied Pvt. Ltd. and Contributors
# See license.txt

import frappe
import unittest
from erpnext_gst_compliance.adequare_integration.adequare_connector import AdequareConnector
from erpnext_gst_compliance.erpnext_gst_compliance.doctype.e_invoice.test_e_invoice import make_e_invoice

class TestAdequareSettings(unittest.TestCase):
	pass

class TestAdequareConnector(unittest.TestCase):
	def setUp(self):
		adequare_settings = frappe.get_single('Adequare Settings')
		adequare_settings.enabled = 1
		adequare_settings.credentials = []
		adequare_settings.append('credentials', {
			'company': '_Test Company',
			'gstin': '27AAECE4835E1ZR',
			'username': 'test',
			'password': 'test'
		})
		adequare_settings.flags.ignore_validate = True
		adequare_settings.save()

		einvoice, _ = make_e_invoice()
		self.connector = AdequareConnector('27AAECE4835E1ZR')
		self.connector.einvoice = einvoice

		self.valid_token_response = {
			"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzY29wZSI6WyJnc3AiXSwiZXhwIjoxNjI4MTYwNTk4LCJhdXRob3JpdGllcyI6WyJST0xFX1NCX0VfQVBJX0VJIl0sImp0aSI6ImNkY2IzNDAxLTkyNWQtNGE2MS1hZDNjLWM3OGJhZGU3NzQwNCIsImNsaWVudF9pZCI6Ijg1OTcxQTYyNTkwNzQ2MjU5MEE5NDY4NjQyNjY0RUY3In0.yeeoX4x5sBq2pGcy_-VN-UugBwgyo446rT2tM62rnlk",
			"token_type": "bearer",
			"expires_in": 2591999,
			"scope": "gsp",
			"jti": "cdcb3401-925d-4a61-ad3c-c78bade77404"
		}

		self.valid_irn_response = {
			"success": True,
			"message": "IRN generated successfully",
			"result": {
				"AckNo": 132110029183779,
				"AckDt": "2021-06-02 19:04:34",
				"Irn": "2dcf96dedb78955d5c2cc44a495b9810d2fbd9509fd970b7a7d3a9dd32799547",
				"SignedInvoice": "eyJhbGciOiJSUzI1NiIsImtpZCI6IkVEQzU3REUxMzU4QjMwMEJBOUY3OTM0MEE2Njk2ODMxRjNDODUwNDciLCJ0eXAiOiJKV1QiLCJ4NXQiOiI3Y1Y5NFRXTE1BdXA5NU5BcG1sb01mUElVRWMifQ.eyJkYXRhIjoie1wiQWNrTm9cIjoxMzIxMTAwMjkxODM3NzksXCJBY2tEdFwiOlwiMjAyMS0wNi0wMiAxOTowNDozNFwiLFwiSXJuXCI6XCIyZGNmOTZkZWRiNzg5NTVkNWMyY2M0NGE0OTViOTgxMGQyZmJkOTUwOWZkOTcwYjdhN2QzYTlkZDMyNzk5NTQ3XCIsXCJWZXJzaW9uXCI6XCIxLjFcIixcIlRyYW5EdGxzXCI6e1wiVGF4U2NoXCI6XCJHU1RcIixcIlN1cFR5cFwiOlwiQjJCXCIsXCJSZWdSZXZcIjpcIk5cIn0sXCJEb2NEdGxzXCI6e1wiVHlwXCI6XCJJTlZcIixcIk5vXCI6XCJTSU5WLTIxLUIyQi0wMDIxXCIsXCJEdFwiOlwiMDIvMDYvMjAyMVwifSxcIlNlbGxlckR0bHNcIjp7XCJHc3RpblwiOlwiMDFBTUJQRzc3NzNNMDAyXCIsXCJMZ2xObVwiOlwiR2xhY2UgVGVjaG5vbG9naWVzXCIsXCJBZGRyMVwiOlwiQWtzaHlhIE5hZ2FyIDFzdCBCbG9jayAxc3QgQ3Jvc3MsIFJhbW11cnRoeSBuYWdhclwiLFwiTG9jXCI6XCJCYW5nYWxvcmVcIixcIlBpblwiOjE5MzUwMixcIlN0Y2RcIjpcIjAxXCJ9LFwiQnV5ZXJEdGxzXCI6e1wiR3N0aW5cIjpcIjM2QUFFQ0YxMTUxQTFaQ1wiLFwiTGdsTm1cIjpcIkVsZWdhbnQgR2xvYmFsXCIsXCJQb3NcIjpcIjM2XCIsXCJBZGRyMVwiOlwiIzUtOS0yODYvMi8yNSwgUmFqaXYgR2FuZGhpIE5hZ2FyLFwiLFwiQWRkcjJcIjpcIlByYXNoYW50aCBOYWdhciwgTW9vc2FwZXQgVmlsbGFnZSxcIixcIkxvY1wiOlwiS3VrYXRwYWxseSwgSHlkZXJhYmFkLFwiLFwiUGluXCI6NTAwMDcyLFwiU3RjZFwiOlwiMzZcIn0sXCJJdGVtTGlzdFwiOlt7XCJJdGVtTm9cIjowLFwiU2xOb1wiOlwiMVwiLFwiSXNTZXJ2Y1wiOlwiTlwiLFwiUHJkRGVzY1wiOlwiQmFza2V0IEJhbGxcIixcIkhzbkNkXCI6XCI5NTA2NjIzMFwiLFwiUXR5XCI6MS4wLFwiVW5pdFwiOlwiTm9zXCIsXCJVbml0UHJpY2VcIjo2MDAuMCxcIlRvdEFtdFwiOjYwMC4wLFwiRGlzY291bnRcIjowLjAsXCJBc3NBbXRcIjo2MDAuMCxcIkdzdFJ0XCI6MTguMCxcIklnc3RBbXRcIjoxMDguMCxcIkNnc3RBbXRcIjowLjAsXCJTZ3N0QW10XCI6MC4wLFwiQ2VzUnRcIjowLjAsXCJDZXNBbXRcIjowLjAsXCJDZXNOb25BZHZsQW10XCI6MC4wLFwiT3RoQ2hyZ1wiOjAuMCxcIlRvdEl0ZW1WYWxcIjo3MDguMH1dLFwiVmFsRHRsc1wiOntcIkFzc1ZhbFwiOjYwMC4wLFwiQ2dzdFZhbFwiOjAuMCxcIlNnc3RWYWxcIjowLjAsXCJJZ3N0VmFsXCI6MTA4LjAsXCJDZXNWYWxcIjowLjAsXCJEaXNjb3VudFwiOjAuMCxcIk90aENocmdcIjowLjAsXCJSbmRPZmZBbXRcIjowLjAsXCJUb3RJbnZWYWxcIjo3MDguMCxcIlRvdEludlZhbEZjXCI6NzA4LjB9fSIsImlzcyI6Ik5JQyJ9.dLpI1jKuCLGrTM9iola09tsAIREQHMkIzgvn4krQqas63pcKygTWemK1zP48IRIlBIxyGDG-s4V8Jy9IDwLAa31ZaR4g69PGdiW8b6Do71nhqnxwVSYPEc62YJ1Hn9w3fgH2mVxHnENYebNbNdqVgTuowCi733VbRc5v55moaBshhB9L6ofWgtZYeP4vjTG-AOttts0paXR4r30wBbneQBOgqLgMHusQY7-XFh3b4qN-0LSXe8lzE_s7-Wl3Ak4idbTwsFWbNEHVNclRwUZ36NvWlEOuUOoLdOCyzyYlwbuCtsco5eck9t0rdu1EnPSZ6CDvBn6lDmVjaBp_A4IMHA",
				"SignedQRCode": "eyJhbGciOiJSUzI1NiIsImtpZCI6IkVEQzU3REUxMzU4QjMwMEJBOUY3OTM0MEE2Njk2ODMxRjNDODUwNDciLCJ0eXAiOiJKV1QiLCJ4NXQiOiI3Y1Y5NFRXTE1BdXA5NU5BcG1sb01mUElVRWMifQ.eyJkYXRhIjoie1wiU2VsbGVyR3N0aW5cIjpcIjAxQU1CUEc3NzczTTAwMlwiLFwiQnV5ZXJHc3RpblwiOlwiMzZBQUVDRjExNTFBMVpDXCIsXCJEb2NOb1wiOlwiU0lOVi0yMS1CMkItMDAyMVwiLFwiRG9jVHlwXCI6XCJJTlZcIixcIkRvY0R0XCI6XCIwMi8wNi8yMDIxXCIsXCJUb3RJbnZWYWxcIjo3MDguMCxcIkl0ZW1DbnRcIjoxLFwiTWFpbkhzbkNvZGVcIjpcIjk1MDY2MjMwXCIsXCJJcm5cIjpcIjJkY2Y5NmRlZGI3ODk1NWQ1YzJjYzQ0YTQ5NWI5ODEwZDJmYmQ5NTA5ZmQ5NzBiN2E3ZDNhOWRkMzI3OTk1NDdcIixcIklybkR0XCI6XCIyMDIxLTA2LTAyIDE5OjA0OjM0XCJ9IiwiaXNzIjoiTklDIn0.nkRNS9Wfb-RQcbSxuOW8XKxdQhr_uYs0AvbYViGmG2VafRv9SrWU1GPcP9RF8UVlrL0OYcUn_BEWqTL3zAPfzTFdeCTi1FKBwlQUjbOIRtkQWuBAEHmL6yDoldKkr3oszNc5YKR7R4Cu8d4cC2PnzJE0TdwOFVm4_g4O2wXkxC1bIUfU88AYeop_uCQ-1nV0sjfBzNB1baEG9mL1DGg7v8US8V_GeM6nMZGsAOPKlz5oZKser0K0L9Pc9V62k41XbveZIBtA6XQBQNpN0tipYMsbbRQnpqnKCv8Kkg_GY58hynalzmn5G7d3Nsthzjsqpan1hXMNZY6c2ums2ktx8A",
				"Status": "ACT",
				"EwbNo": None,
				"EwbDt": None,
				"EwbValidTill": None,
				"Remarks": None
			}
		}

		self.invalid_irn_response = {
			"success": False,
			"message": "2258 : Supplier GSTIN state codedoes not match with the state code passed in supplier details"
		}

		self.valid_irn_cancel_response = {
			"success": True,
			"message": "E-Invoice is cancelled successfully",
			"result": {
				"Irn": "2dcf96dedb78955d5c2cc44a495b9810d2fbd9509fd970b7a7d3a9dd32799547",
				"CancelDate": "2021-03-04 11:20:00"
			}
		}

		self.invalid_irn_cancel_response = {
			"success": False,
			"message": "2270 : The allowed cancellation time limit is crossed, you cannot cancel the IRN"
		}

	def test_token_generation(self):
		self.assertFalse(self.connector.settings.token_expiry)
		response = frappe._dict(self.valid_token_response)
		self.connector.handle_successful_token_generation(response)
		self.assertTrue(self.connector.settings.auth_token)
		self.assertTrue(self.connector.settings.token_expiry)
	
	def test_irn_generation(self):
		# with successful response
		response = frappe._dict(self.valid_irn_response)
		success, errors = self.connector.handle_irn_generation_response(response)
		self.assertTrue(success)
		self.assertEqual(self.connector.einvoice.irn, response.result.get('Irn'))
		self.assertEqual(self.connector.einvoice.ack_no, response.result.get('AckNo'))
		self.assertEqual(self.connector.einvoice.ack_date, response.result.get('AckDt'))
		self.assertEqual(self.connector.einvoice.status, 'IRN Generated')

		# with error response
		response = frappe._dict(self.invalid_irn_response)
		success, errors = self.connector.handle_irn_generation_response(response)
		self.assertFalse(success)
		self.assertEqual(len(errors), 1)
	
	def test_irn_cancellation(self):
		# with successful response
		response = frappe._dict(self.valid_irn_response)
		success, errors = self.connector.handle_irn_cancellation_response(response)
		self.assertTrue(success)
		self.assertEqual(self.connector.einvoice.irn_cancelled, 1)
		self.assertEqual(self.connector.einvoice.irn_cancel_date, response.result.get('CancelDate'))
		self.assertEqual(self.connector.einvoice.status, 'IRN Cancelled')

		# with error response
		response = frappe._dict(self.invalid_irn_cancel_response)
		success, errors = self.connector.handle_irn_cancellation_response(response)
		self.assertFalse(success)
		self.assertEqual(len(errors), 1)

	def tearDown(self):
		adequare_settings = frappe.get_single('Adequare Settings')
		adequare_settings.enabled = 0
		adequare_settings.auth_token = None
		adequare_settings.token_expiry = None
		adequare_settings.flags.ignore_validate = True
		adequare_settings.save()