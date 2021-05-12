# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.data import get_link_to_form

class EInvoicingSettings(Document):
	def validate(self):
		if not frappe.db.get_single_value(self.service_provider, 'enabled'):
			settings_form = get_link_to_form(self.service_provider, self.service_provider)
			frappe.throw(_('Selected Service Provider is disabled. Please enable it by visitng {} Form.').format(
				settings_form
			))

