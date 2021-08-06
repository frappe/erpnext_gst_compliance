# ERPNext GST Compliance

Manage GST Compliance of ERPNext for India

## Features
### E Invoicing

E-Invoicing in ERPNext is automated using API integration with two GST Suvidha Providers (GSP):
1. Adequare GSP
2. Cleartax

Both of these providers enables one-click e-invoice generation & cancellation. 

**Installation**
1. You must have a working ERPNext site either on a local bench setup or hosted on Frappe Cloud.
2. For a local bench setup, install this app with Bench CLI
    ```
    bench get-app https://github.com/frappe/erpnext_gst_compliance.git
    bench --site site_name install-app erpnext_gst_compliance
    ```
3. For a site hosted on Frappe Cloud, follow [this](https://frappecloud.com/docs/bench/install-custom-app) guide to add this app to your custom bench. Then simply install this app on to your hosted site.
4. Once you have this app install on your site, you can follow [this](https://docs.erpnext.com/docs/v13/user/manual/en/regional/india/setup-e-invoicing) guide to configure API integration.

#### License

MIT