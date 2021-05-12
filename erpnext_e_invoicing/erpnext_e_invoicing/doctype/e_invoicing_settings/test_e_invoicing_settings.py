# Copyright (c) 2021, Frappe and Contributors
# See license.txt

import frappe
import unittest

class TestEInvoicingSettings(unittest.TestCase):

	def test_service_provider_is_disabled(self):
		e_invoicing_settings = frappe.get_doc('E Invoicing Settings')
		e_invoicing_settings.service_provider = 'Cleartax Settings'
		self.assertRaises(frappe.ValidationError, e_invoicing_settings.save)
