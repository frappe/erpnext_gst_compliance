# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.data import get_link_to_form
from erpnext_gst_compliance.cleartax_integration.cleartax_connector import CleartaxConnector

class CleartaxSettings(Document):
	def validate(self):
		if not self.enabled:
			return

		for row in self.credentials:
			gstin_company = self.get_company_linked_with_gstin(row.gstin)
			if not gstin_company:
				msg = _("The entered GSTIN {} doesn't matches with Company GSTIN.").format(row.gstin) + ' '
				msg += _("Please ensure that company address has proper GSTIN set that matches with entered GSTIN.")
				frappe.throw(msg, title=_('Invalid GSTIN'))
	
	def on_update(self):
		current_service_provider = frappe.db.get_single_value('E Invoicing Settings', 'service_provider')
		if self.enabled and current_service_provider != self.name:
			link_to_settings = get_link_to_form('E Invoicing Settings', 'E Invoicing Settings')
			frappe.msgprint(
				_('You must set Cleartax as E-Invoicing Service Provider in {} to use it for e-invoicing.')
					.format(link_to_settings), title=_('Set as Default Provider'))
	
	def get_company_linked_with_gstin(self, gstin):
		company_name = frappe.db.sql("""
			select dl.link_name from `tabAddress` a, `tabDynamic Link` dl
			where a.gstin = %s and dl.parent = a.name and dl.link_doctype = 'Company'
		""", (gstin))

		return company_name[0][0] if company_name and len(company_name) > 0 else None

	def get_connector(self):
		return CleartaxConnector