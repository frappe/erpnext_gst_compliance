# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
from erpnext.accounts.doctype.sales_invoice.test_sales_invoice import get_sales_invoice_for_e_invoice

class TestEInvoice(unittest.TestCase):
	def setUp(self):
		self.e_invoice, self.sales_invoice = make_e_invoice()
		self.assertEqual(self.e_invoice.status, 'IRN Pending')

	def test_mandatory_fields(self):
		mandatory_fields = []
		party_fields = [
			'seller_gstin', 'seller_legal_name', 'seller_address_line_1', 'seller_location',
			'seller_pincode', 'seller_state_code', 'buyer_gstin', 'buyer_legal_name', 'buyer_address_line_1',
			'buyer_location', 'buyer_pincode', 'buyer_state_code', 'buyer_place_of_supply'
		]
		if self.e_invoice.dispatch_legal_name:
			party_fields += [
				'dispatch_legal_name', 'dispatch_address_line_1', 'dispatch_location',
				'dispatch_pincode', 'dispatch_state_code'
			]
		if self.e_invoice.shipping_legal_name:
			party_fields += [
				'shipping_legal_name', 'shipping_address_line_1', 'shipping_location',
				'shipping_pincode', 'shipping_state_code'
			]

		mandatory_fields += party_fields
		mandatory_fields += ['ass_value', 'base_invoice_value']
		if self.sales_invoice.transporter:
			mandatory_fields += ['distance']

		for key in mandatory_fields:
			self.assertTrue(self.e_invoice.get(key))

	def test_party_details(self):
		self.assertEqual(self.e_invoice.seller_legal_name, self.sales_invoice.company)
		self.assertEqual(self.e_invoice.seller_gstin, '27AAECE4835E1ZR')
		self.assertEqual(self.e_invoice.seller_pincode, '401108')
		self.assertEqual(self.e_invoice.seller_state_code, '27')
		self.assertEqual(self.e_invoice.buyer_legal_name, self.sales_invoice.customer)
		self.assertEqual(self.e_invoice.buyer_gstin, '27AACCM7806M1Z3')
		self.assertEqual(self.e_invoice.buyer_pincode, '410038')
		self.assertEqual(self.e_invoice.buyer_place_of_supply, '27')

	def test_item_validations(self):
		item = self.e_invoice.items[0]
		self.assertEqual(item.hsn_code, '990002')
		# if hsn_code starts with 99 then its a service item
		self.assertTrue(item.is_service_item)
		self.assertEqual(item.quantity, 2000)

		item = self.e_invoice.items[1]
		self.assertEqual(item.hsn_code, '890002')
		# if hsn_code doesn't starts with 99 then not a service item
		self.assertFalse(item.is_service_item)
		self.assertEqual(item.quantity, 420)

		self.e_invoice.validate_items()

		gst_rate_copy = self.e_invoice.items[0].gst_rate
		# invalid gst rate should throw an error
		self.e_invoice.items[0].gst_rate = 12.5
		self.assertRaises(frappe.ValidationError, self.e_invoice.validate_items)
		self.e_invoice.items[0].gst_rate = gst_rate_copy

	def test_invalid_uom(self):
		item = self.e_invoice.items[0]
		item.unit = 'BAGS'
		self.assertRaises(frappe.ValidationError, self.e_invoice.save)

		self.e_invoice.reload()
		item = self.e_invoice.items[0]
		item.unit = 'BAG'
		self.e_invoice.save()

def make_e_invoice():
	sales_invoice = get_sales_invoice_for_e_invoice()
	sales_invoice.items[0].gst_hsn_code = "990002"
	sales_invoice.items[1].gst_hsn_code = "890002"
	sales_invoice.save()

	e_invoice = frappe.new_doc('E Invoice')
	e_invoice.invoice = sales_invoice.name
	e_invoice.sync_with_sales_invoice()
	e_invoice.save()

	return e_invoice, sales_invoice