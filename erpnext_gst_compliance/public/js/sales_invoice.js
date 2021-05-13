frappe.ui.form.on('Sales Invoice', {
	async refresh(frm) {
		const invoice_eligible = await get_einvoice_eligibility(frm.doc);

		if (!invoice_eligible) return;

		const { irn, irn_cancelled, ewaybill, eway_bill_cancelled, __unsaved } = frm.doc;

		const add_einvoice_button = (label, action) => {
			if (!frm.custom_buttons[label]) {
				frm.add_custom_button(label, action, __('Cleartax'));
			}
		};
		
		const e_invoicing_settings_path = 'erpnext_e_invoicing.erpnext_e_invoicing.doctype.e_invoicing_settings.e_invoicing_settings';

		// Generate IRN
		add_einvoice_button(__('Generate IRN'), async () => {
			await frm.reload_doc();
			frappe.call({
				method: e_invoicing_settings_path + '.generate_irn',
				args: { sales_invoice: frm.doc },
				callback: () => frm.reload_doc(),
				freeze: true
			});
		});

		// Cancel IRN
		const fields = get_irn_cancellation_fields();
		const action = () => {
			const d = new frappe.ui.Dialog({
				title: __("Cancel IRN"),
				fields: fields,
				primary_action: function() {
					const data = d.get_values();
					frappe.call({
						method: e_invoicing_settings_path + '.cancel_irn',
						args: {
							sales_invoice: frm.doc,
							reason: data.reason.split('-')[0],
							remark: data.remark
						},
						freeze: true,
						callback: () => frm.reload_doc() || d.hide(),
						error: () => d.hide()
					});
				},
				primary_action_label: __('Submit')
			});
			d.show();
		};
		add_einvoice_button(__('Cancel IRN'), action);

		if (irn && !irn_cancelled && !ewaybill) {
			// Generate E-Way Bill
		}

		if (irn && ewaybill && !irn_cancelled && !eway_bill_cancelled) {
			// Cancel E-Way Bill
		}
	}
});

const get_einvoice_eligibility = async (doc) => {
	frappe.dom.freeze();
	const { message: invoice_eligible } = await frappe.call({
		method: 'erpnext_e_invoicing.utils.validate_einvoice_eligibility',
		args: { doc: doc },
		debounce: 2000
	});
	frappe.dom.unfreeze();

	return invoice_eligible;
}

const get_irn_cancellation_fields = () => {
	return [
		{
			"label": "Reason",
			"fieldname": "reason",
			"fieldtype": "Select",
			"reqd": 1,
			"default": "1-Duplicate",
			"options": ["1-Duplicate", "2-Data Entry Error", "3-Order Cancelled", "4-Other"]
		},
		{
			"label": "Remark",
			"fieldname": "remark",
			"fieldtype": "Data",
			"reqd": 1
		}
	];
}