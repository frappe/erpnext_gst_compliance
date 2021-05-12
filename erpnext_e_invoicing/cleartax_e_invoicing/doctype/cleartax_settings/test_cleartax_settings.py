# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

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
