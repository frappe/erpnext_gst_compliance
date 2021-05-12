from . import __version__ as app_version

app_name = "erpnext_gst_compliance"
app_title = "ERPNext GST Compliance"
app_publisher = "Frappe Technologied Pvt. Ltd."
app_description = "Manage GST Compliance of ERPNext"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "developers@erpnext.com"
app_license = "MIT"

doctype_js = {
	"Sales Invoice": "public/js/sales_invoice.js"
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
