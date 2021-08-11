import frappe

def execute():
	if frappe.db.exists('E Invoice Settings'):
		credentials = frappe.db.get_all('E Invoice User', fields=['*'])
		if not credentials:
			return

		adequare_settings = frappe.get_single('Adequare Settings')
		for credential in credentials:
			adequare_settings.append('credentials', {
				'company': credential.company,
				'gstin': credential.gstin,
				'username': credential.username,
				'password': credential.password
			})
		adequare_settings.enabled = 1
		adequare_settings.sandbox_mode = credential.sandbox_mode
		adequare_settings.save()

