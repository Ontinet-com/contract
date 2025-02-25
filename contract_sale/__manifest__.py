# Copyright 2017 Tecnativa - Luis M. Ontalba
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Contract from Sale",
    "version": "17.0.1.0.0",
    "category": "Sales",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/contract",
    "depends": ["sale", "contract"],
    "development_status": "Production/Stable",
    "data": [
        "security/ir.model.access.csv",
        "security/contract_security.xml",
        "views/contract.xml",
        "views/res_partner_view.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
}
