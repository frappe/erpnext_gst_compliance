// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// render
frappe.listview_settings['E Invoice'] = {
	has_indicator_for_draft: 1,
	get_indicator: function(doc) {
		var status_color = {
			"IRN Pending": "yellow",
			"IRN Generated": "green",
			"E-Way Bill Generated": "green",
			"IRN Cancelled": "red",
            "Cancelled": "red"
		};
		return [__(doc.status), status_color[doc.status], "status,=,"+doc.status];
	}
};
