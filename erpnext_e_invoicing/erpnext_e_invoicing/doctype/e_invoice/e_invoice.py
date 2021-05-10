# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

from json import loads, dumps

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.data import cint, format_date

from erpnext.regional.india.utils import get_gst_accounts

class EInvoice(Document):
	def validate(self):
		pass

	@frappe.whitelist()
	def fetch_invoice_details(self):
		self.set_sales_invoice()
		self.set_invoice_type()
		self.set_supply_type()
		self.set_seller_details()
		self.set_buyer_details()
		self.set_shipping_details()
		self.set_item_details()
		self.set_value_details()
		self.set_payment_details()
		self.set_return_doc_reference()
		self.set_eway_bill_details()

	def set_sales_invoice(self):
		self.sales_invoice = frappe.get_doc('Sales Invoice', self.invoice)

	def set_invoice_type(self):
		self.invoice_type = 'CRN' if self.sales_invoice.is_return else 'INV'

	def set_supply_type(self):
		gst_category = self.sales_invoice.gst_category

		if gst_category == 'Registered Regular': self.supply_type = 'B2B'
		elif gst_category == 'SEZ': self.supply_type = 'SEZWOP'
		elif gst_category == 'Overseas': self.supply_type = 'EXPWOP'
		elif gst_category == 'Deemed Export': self.supply_type = 'DEXP'

	def set_seller_details(self):
		company_address = self.sales_invoice.company_address
		if not company_address:
			frappe.throw(_('Company address must be set to be able to generate e-invoice.'))

		seller_address = frappe.get_all('Address', {'name': company_address}, ['*'])[0]
		if not seller_address.gstin:
			frappe.throw(_('Company address {} must have GSTIN set to be able to generate e-invoice.').format(company_address))

		self.seller_legal_name = self.company
		self.seller_gstin = seller_address.gstin
		self.seller_location = seller_address.city
		self.seller_pincode = seller_address.pincode
		self.seller_address_line_1 = seller_address.address_line1
		self.seller_address_line_2 = seller_address.address_line2
		self.seller_state_code = seller_address.gst_state_number

	def set_buyer_details(self):
		customer_address = self.sales_invoice.customer_address
		if not customer_address:
			frappe.throw(_('Customer address must be set to be able to generate e-invoice.'))

		is_export = self.supply_type == 'EXPWOP'
		buyer_address = frappe.get_all('Address', {'name': customer_address}, ['*'])[0]

		if not buyer_address.gstin and not is_export:
			frappe.throw(_('Customer address {} must have GSTIN set to be able to generate e-invoice.').format(customer_address))

		self.buyer_legal_name = self.sales_invoice.customer
		self.buyer_gstin = buyer_address.gstin
		self.buyer_location = buyer_address.city
		self.buyer_pincode = buyer_address.pincode
		self.buyer_address_line_1 = buyer_address.address_line1
		self.buyer_address_line_2 = buyer_address.address_line2
		self.buyer_state_code = buyer_address.gst_state_number
		self.buyer_place_of_supply = buyer_address.gst_state_number

		if is_export:
			self.buyer_gstin = 'URP'
			self.buyer_state_code = 96
			self.buyer_pincode = 999999
			self.buyer_place_of_supply = 96
	
	def set_shipping_details(self):
		shipping_address_name = self.sales_invoice.shipping_address_name
		if shipping_address_name:
			is_export = self.supply_type == 'EXPWOP'
			shipping_address = frappe.get_all('Address', {'name': shipping_address_name}, ['*'])[0]

			self.shipping_legal_name = shipping_address.address_title
			self.shipping_gstin = shipping_address.gstin
			self.shipping_location = shipping_address.city
			self.shipping_pincode = shipping_address.pincode
			self.shipping_address_line_1 = shipping_address.address_line1
			self.shipping_address_line_2 = shipping_address.address_line2
			self.shipping_state_code = shipping_address.gst_state_number

			if is_export:
				self.shipping_gstin = 'URP'
				self.shipping_state_code = 96
				self.shipping_pincode = 999999
				self.shipping_place_of_supply = 96

	def get_invoice_discount_type(self):
		if self.sales_invoice.discount_amount:
			return self.sales_invoice.apply_discount_on

		return ''

	def set_item_details(self):
		self.items = []
		discount_applied_on_net_total = self.get_invoice_discount_type() == 'Net Total'

		for item in self.sales_invoice.items:
			is_service_item = frappe.db.get_value('Item', item.item_code, 'is_stock_item')
			discount = abs(item.base_amount - item.base_net_amount) if discount_applied_on_net_total else 0

			einvoice_item = frappe._dict({
				'item_code': item.item_code,
				'item_name': item.item_name,
				'is_service_item': is_service_item,
				'hsn_code': item.gst_hsn_code,
				'quantity': abs(item.qty),
				'discount': discount,
				'unit': item.uom,
				'rate': abs((abs(item.taxable_value) - discount) / item.qty),
				'amount': abs(item.taxable_value) + discount,
				'taxable_value': abs(item.taxable_value)
			})

			self.set_item_tax_details(einvoice_item)

			einvoice_item.total_item_value = abs(
				einvoice_item.taxable_value + einvoice_item.igst_amount +
				einvoice_item.sgst_amount + einvoice_item.cgst_amount + 
				einvoice_item.cess_amount + einvoice_item.cess_nadv_amount +
				einvoice_item.other_charges
			)
			self.append('items', einvoice_item)

	def set_item_tax_details(self, item):
		gst_accounts = get_gst_accounts(self.company)
		gst_accounts_list = [d for accounts in gst_accounts.values() for d in accounts if d]

		for attr in ['gst_rate', 'cgst_amount',  'sgst_amount', 'igst_amount',
			'cess_rate', 'cess_amount', 'cess_nadv_amount', 'other_charges']:
			item[attr] = 0

		for t in self.sales_invoice.taxes:
			is_applicable = t.tax_amount and t.account_head in gst_accounts_list
			if is_applicable:
				# this contains item wise tax rate & tax amount (incl. discount)
				item_tax_detail = loads(t.item_wise_tax_detail).get(item.item_code or item.item_name)

				item_tax_rate = item_tax_detail[0]
				# item tax amount excluding discount amount
				item_tax_amount = (item_tax_rate / 100) * item.taxable_value

				if t.account_head in gst_accounts.cess_account:
					item_tax_amount_after_discount = item_tax_detail[1]
					if t.charge_type == 'On Item Quantity':
						item.cess_nadv_amount += abs(item_tax_amount_after_discount)
					else:
						item.cess_rate += item_tax_rate
						item.cess_amount += abs(item_tax_amount_after_discount)

				for tax_type in ['igst', 'cgst', 'sgst']:
					if t.account_head in gst_accounts[f'{tax_type}_account']:
						item.gst_rate += item_tax_rate
						item[f'{tax_type}_amount'] += abs(item_tax_amount)
			else:
				# TODO: other charges per item
				pass

	def set_value_details(self):
		invoice_value_details = frappe._dict(dict())

		if self.get_invoice_discount_type() == 'Net Total':
			# Discount already applied on net total which means on items
			self.ass_value = abs(sum([i.taxable_value for i in self.get('items')]))
			self.invoice_discount = 0
		elif self.get_invoice_discount_type() == 'Grand Total':
			self.ass_value = abs(sum([i.taxable_value for i in self.get('items')]))
			self.invoice_discount = self.sales_invoice.base_discount_amount
		else:
			# no invoice level discount applied
			self.ass_value = abs(sum([i.taxable_value for i in self.get('items')]))
			self.invoice_discount = 0

		self.round_off_amount = self.sales_invoice.base_rounding_adjustment
		self.base_invoice_value = abs(self.sales_invoice.base_rounded_total) or abs(self.sales_invoice.base_grand_total)
		self.invoice_value = abs(self.sales_invoice.rounded_total) or abs(self.sales_invoice.grand_total)

		self.set_invoice_tax_details()

	def set_invoice_tax_details(self):
		gst_accounts = get_gst_accounts(self.company)
		gst_accounts_list = [d for accounts in gst_accounts.values() for d in accounts if d]

		self.cgst_value = 0
		self.sgst_value = 0
		self.igst_value = 0
		self.cess_value = 0
		self.other_charges = 0
		considered_rows = []

		for t in self.sales_invoice.taxes:
			tax_amount = t.base_tax_amount if self.get_invoice_discount_type() == 'Grand Total' \
							else t.base_tax_amount_after_discount_amount

			if t.account_head in gst_accounts_list:
				if t.account_head in gst_accounts.cess_account:
					# using after discount amt since item also uses after discount amt for cess calc
					self.cess_value += abs(t.base_tax_amount_after_discount_amount)

				for tax in ['igst', 'cgst', 'sgst']:
					if t.account_head in gst_accounts[f'{tax}_account']:
						new_value = self.get(f'{tax}_value') + abs(tax_amount)
						self.set(f'{tax}_value', new_value)

					self.update_other_charges(t, gst_accounts_list, considered_rows)
			else:
				self.other_charges += abs(tax_amount)
	
	def update_other_charges(self, tax_row, gst_accounts_list, considered_rows):
		taxes = self.sales_invoice.get('taxes')
		prev_row_id = cint(tax_row.row_id) - 1

		if tax_row.account_head in gst_accounts_list and prev_row_id not in considered_rows:
			if tax_row.charge_type == 'On Previous Row Amount':
				amount = taxes[prev_row_id].tax_amount_after_discount_amount
				self.other_charges -= abs(amount)
				considered_rows.append(prev_row_id)
			if tax_row.charge_type == 'On Previous Row Total':
				amount = taxes[prev_row_id].base_total - self.sales_invoice.base_net_total
				self.other_charges -= abs(amount)
				considered_rows.append(prev_row_id)

	def set_payment_details(self):
		if self.sales_invoice.is_pos and self.sales_invoice.base_paid_amount:
			self.payee_name = self.company
			self.mode = ', '.join([d.mode_of_payment for d in self.sales_invoice.payments if d.amount > 0])
			self.paid_amount = self.sales_invoice.base_paid_amount
			self.outstanding_amount = self.sales_invoice.outstanding_amount

	def set_return_doc_reference(self):
		if self.sales_invoice.is_return:
			if not self.sales_invoice.return_against:
				frappe.throw(_('For generating IRN, reference to the original invoice is mandatory for a credit note. Please set {} field to generate e-invoice.')
					.format(frappe.bold('Return Against')), title=_('Missing Field'))

			self.previous_document_no = self.sales_invoice.return_against
			original_invoice_date = frappe.db.get_value('Sales Invoice', self.sales_invoice.return_against, 'posting_date')
			self.previous_document_date = format_date(original_invoice_date, 'dd/mm/yyyy')

	def set_eway_bill_details(self):
		if self.sales_invoice.transporter:
			if self.sales_invoice.is_return:
				frappe.throw(_('E-Way Bill cannot be generated for Credit Notes & Debit Notes. Please clear fields in the Transporter Section of the invoice.'),
					title=_('Invalid Fields'))

			mode_of_transport = {'Road': '1', 'Air': '2', 'Rail': '3', 'Ship': '4'}
			vehicle_type = {'': '', 'Regular': 'R', 'Over Dimensional Cargo (ODC)': 'O'}

			self.tranporter_gstin = self.sales_invoice.gst_transporter_id,
			self.transporter_name = self.sales_invoice.transporter_name,
			self.mode_of_transport = mode_of_transport[self.sales_invoice.mode_of_transport],
			self.distance = self.sales_invoice.distance or 0,
			self.transport_document_no = self.sales_invoice.lr_no,
			self.transport_document_date = format_date(self.sales_invoice.lr_date, 'dd/mm/yyyy'),
			self.vehicle_no = self.sales_invoice.vehicle_no,
			self.vehicle_type = vehicle_type[self.sales_invoice.gst_vehicle_type]

