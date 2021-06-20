frappe.ui.form.on('Sales Invoice', {
	async refresh(frm) {
		const invoice_eligible = await get_einvoice_eligibility(frm.doc);

		if (!invoice_eligible) return;

		const { e_invoice_status } = frm.doc;

		const add_einvoice_button = (label, action) => {
			if (!frm.custom_buttons[label]) {
				frm.add_custom_button(label, action, __('E-Invoicing'));
			}
		};
		
		const e_invoicing_controller = 'erpnext_gst_compliance.erpnext_gst_compliance.e_invoicing_controller';

		if (!e_invoice_status || e_invoice_status == 'IRN Pending') {
			// Generate IRN
			add_einvoice_button(__('Generate IRN'), async () => {
				if (frm.is_dirty()) return raise_form_is_dirty_error();

				await frm.reload_doc();
				frappe.call({
					method: e_invoicing_controller + '.generate_irn',
					args: { sales_invoice: frm.doc },
					callback: () => frm.reload_doc(),
					error: () => frm.reload_doc(),
					freeze: true
				});
			});
		}


		if (e_invoice_status == 'IRN Generated') {
			// Cancel IRN
			const fields = get_irn_cancellation_fields();
			const action = () => {
				if (frm.is_dirty()) return raise_form_is_dirty_error();

				const d = new frappe.ui.Dialog({
					title: __("Cancel IRN"),
					fields: fields,
					primary_action: function() {
						const data = d.get_values();
						frappe.call({
							method: e_invoicing_controller + '.cancel_irn',
							args: {
								sales_invoice: frm.doc,
								reason: data.reason.split('-')[0],
								remark: data.remark
							},
							freeze: true,
							callback: () => {
								frm.reload_doc();
								d.hide();
							},
							error: () => d.hide()
						});
					},
					primary_action_label: __('Submit')
				});
				d.show();
			};
			add_einvoice_button(__('Cancel IRN'), action);
		}

		if (e_invoice_status == 'IRN Generated') {
			// Generate E-Way Bill
			const action = () => {
				const d = new frappe.ui.Dialog({
					title: __('Generate E-Way Bill'),
					size: "large",
					fields: get_eway_bill_fields(frm),
					primary_action: function() {
						const data = d.get_values();
						frappe.call({
							method: e_invoicing_controller + '.generate_eway_bill',
							args: {
								sales_invoice_name: frm.doc.name,
								...data
							},
							freeze: true,
							callback: () => {
								frm.reload_doc();
								d.hide();
							},
							error: () => d.hide()
						});
					},
					primary_action_label: __('Submit')
				});
				d.show();
			};

			add_einvoice_button(__("Generate E-Way Bill"), action);
		}

		if (e_invoice_status == 'E-Way Bill Generated') {
			// Cancel E-Way Bill
		}
	}
});

const get_einvoice_eligibility = async (doc) => {
	frappe.dom.freeze();
	const { message: invoice_eligible } = await frappe.call({
		method: 'erpnext_gst_compliance.utils.validate_einvoice_eligibility',
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

const raise_form_is_dirty_error = () => {
	frappe.throw({
		message: __('You must save the document before making e-invoicing request.'),
		title: __('Unsaved Document')
	});
}

const get_eway_bill_fields = () => {
	return [
		{
			'fieldname': 'transporter',
			'label': 'Transporter',
			'fieldtype': 'Link',
			'options': 'Supplier'
		},
		{
			'fieldname': 'transporter_gstin',
			'label': 'GST Transporter ID',
			'fieldtype': 'Data',
			'fetch_from': 'transporter.gst_transporter_id'
		},
		{
			'fieldname': 'transport_document_no',
			'label': 'Transport Receipt No',
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'vehicle_no',
			'label': 'Vehicle No',
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'distance',
			'label': 'Distance (in km)',
			'fieldtype': 'Float'
		},
		{
			'fieldname': 'transporter_col_break',
			'fieldtype': 'Column Break',
		},
		{
			'fieldname': 'transporter_name',
			'label': 'Transporter Name',
			'fieldtype': 'Data',
			'fetch_from': 'transporter.name'
		},
		{
			'fieldname': 'mode_of_transport',
			'label': 'Mode of Transport',
			'fieldtype': 'Select',
			'options': `\nRoad\nAir\nRail\nShip`
		},
		{
			'fieldname': 'transport_document_date',
			'label': 'Transport Receipt Date',
			'fieldtype': 'Date'
		},
		{
			'fieldname': 'vehicle_type',
			'label': 'GST Vehicle Type',
			'fieldtype': 'Select',
			'options': `\nRegular\nOver Dimensional Cargo (ODC)`,
			'depends_on': 'eval:(doc.mode_of_transport === "Road")',
			'default': ''
		}
	];
};