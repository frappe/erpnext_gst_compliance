// Copyright (c) 2021, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on('E Invoicing Settings', {
	onload: async (frm) => {
		let einvoicing_modules = await frappe.db.get_list('Module Def', {
			filters: {
				app_name: 'erpnext_gst_compliance'
			}
		});
		if (einvoicing_modules && einvoicing_modules.length) {
			einvoicing_modules = einvoicing_modules.map(m => m.name)
		} else {
			return;
		}

		let service_providers = await frappe.db.get_list('DocType', {
			filters: {
				module: ['in', einvoicing_modules],
				name: ['!=', frm.doc.doctype],
				issingle: 1
			}
		});

		if (service_providers && service_providers.length) {
			service_providers = service_providers.map(p => p.name);
		}

		frm.set_query('service_provider', () => {
			return {
				filters: {
					issingle: 1,
					name: ['in', service_providers]
				}
			}
		});
	},

	refresh(frm) {
		if (frm.doc.service_provider) {
			const label = __('Go to {0}', [frm.doc.service_provider])
			frm.add_custom_button(label, function() {
				frappe.set_route('Form', frm.doc.service_provider);
			});
		}
	}
});
