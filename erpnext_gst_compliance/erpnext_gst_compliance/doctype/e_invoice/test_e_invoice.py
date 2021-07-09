# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
from erpnext.accounts.doctype.sales_invoice.test_sales_invoice import get_sales_invoice_for_e_invoice

class TestEInvoice(unittest.TestCase):
	def setUp(self):
		self.sales_invoice = get_sales_invoice_for_e_invoice()
		self.sales_invoice.save()

		self.e_invoice = frappe.new_doc('E Invoice')
		self.e_invoice.invoice = self.sales_invoice.name
		self.e_invoice.sync_with_sales_invoice()


	def test_invalid_uom(self):
		item = self.e_invoice.items[0]
		item.unit = 'BAGS'
		self.assertRaises(frappe.ValidationError, self.e_invoice.save)

		item = self.e_invoice.items[0]
		item.unit = 'BAG'
		self.e_invoice.save()