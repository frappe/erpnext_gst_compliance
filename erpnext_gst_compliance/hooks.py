from . import __version__ as app_version

app_name = "erpnext_gst_compliance"
app_title = "ERPNext GST Compliance"
app_publisher = "Frappe Technologied Pvt. Ltd."
app_description = "Manage GST Compliance of ERPNext"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "developers@erpnext.com"
app_license = "MIT"

before_tests = "erpnext.setup.utils.before_tests"
after_install = "erpnext_gst_compliance.erpnext_gst_compliance.setup.setup"

doctype_js = {
	"Sales Invoice": "public/js/sales_invoice.js"
}

doc_events = {
	"Sales Invoice": {
		"on_update": "erpnext_gst_compliance.erpnext_gst_compliance.doctype.e_invoice.e_invoice.validate_sales_invoice_change",
		"on_submit": "erpnext_gst_compliance.erpnext_gst_compliance.doctype.e_invoice.e_invoice.validate_sales_invoice_submission",
		"on_cancel": [
			"erpnext_gst_compliance.erpnext_gst_compliance.doctype.e_invoice.e_invoice.validate_sales_invoice_cancellation",
			"erpnext_gst_compliance.erpnext_gst_compliance.doctype.e_invoice.e_invoice.cancel_e_invoice"
		],
		"on_trash": [
			"erpnext_gst_compliance.erpnext_gst_compliance.doctype.e_invoice.e_invoice.validate_sales_invoice_deletion",
			"erpnext_gst_compliance.erpnext_gst_compliance.doctype.e_invoice.e_invoice.delete_e_invoice"
		]
	},
	"Company": {
		"after_insert": "erpnext_gst_compliance.erpnext_gst_compliance.setup.on_company_update",
		"on_update": "erpnext_gst_compliance.erpnext_gst_compliance.setup.on_company_update"
	}
}

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]
