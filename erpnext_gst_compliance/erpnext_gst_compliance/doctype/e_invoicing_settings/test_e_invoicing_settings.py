# Copyright (c) 2021, Frappe and Contributors
# See license.txt

import frappe
import unittest

class TestEInvoicingSettings(unittest.TestCase):
	def test_service_provider_is_disabled(self):
		e_invoicing_settings = frappe.get_doc('E Invoicing Settings')
		e_invoicing_settings.service_provider = 'Adequare Settings'
		self.assertRaises(frappe.ValidationError, e_invoicing_settings.save)

		adequare_settings = frappe.get_single('Adequare Settings')
		adequare_settings.enabled = 1
		adequare_settings.flags.ignore_validate = True
		adequare_settings.save()

		e_invoicing_settings.reload()
		e_invoicing_settings.service_provider = 'Adequare Settings'
		e_invoicing_settings.save()

		adequare_settings.reload()
		adequare_settings.enabled = 0
		adequare_settings.flags.ignore_validate = True
		adequare_settings.save()

		e_invoicing_settings.reload()
		e_invoicing_settings.service_provider = None
		e_invoicing_settings.flags.ignore_mandatory = True
		e_invoicing_settings.save()