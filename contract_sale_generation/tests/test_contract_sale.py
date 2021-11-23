# © 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# Copyright 2017 Pesol (<http://pesol.es>)
# Copyright 2017 Angel Moya <angel.moya@pesol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import Form
from odoo.tests.common import SavepointCase


def to_date(date):
    return fields.Date.to_date(date)


class TestContractSale(SavepointCase):
    # Use case : Prepare some data for current test case

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {
                "name": "Contracts",
            }
        )
        contract_date = "2020-01-15"
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "pricelist for contract test",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "partner test contract",
                "property_product_pricelist": cls.pricelist.id,
            }
        )
        cls.product_1 = cls.env.ref("product.product_product_1")
        cls.product_1.taxes_id += cls.env["account.tax"].search(
            [("type_tax_use", "=", "sale")], limit=1
        )
        cls.product_1.description_sale = "Test description sale"
        cls.line_template_vals = {
            "product_id": cls.product_1.id,
            "name": "Test Contract Template",
            "quantity": 1,
            "uom_id": cls.product_1.uom_id.id,
            "price_unit": 100,
            "discount": 50,
            "recurring_rule_type": "yearly",
            "recurring_interval": 1,
        }
        cls.template_vals = {
            "name": "Test Contract Template",
            "contract_type": "sale",
            "contract_line_ids": [
                (0, 0, cls.line_template_vals),
            ],
        }
        cls.template = cls.env["contract.template"].create(cls.template_vals)
        # For being sure of the applied price
        cls.env["product.pricelist.item"].create(
            {
                "pricelist_id": cls.partner.property_product_pricelist.id,
                "product_id": cls.product_1.id,
                "compute_price": "formula",
                "base": "list_price",
            }
        )
        cls.contract = cls.env["contract.contract"].create(
            {
                "name": "Test Contract",
                "partner_id": cls.partner.id,
                "pricelist_id": cls.partner.property_product_pricelist.id,
                "generation_type": "sale",
                "sale_autoconfirm": False,
                "group_id": cls.analytic_account.id,
            }
        )
        cls.line_vals = {
            # "contract_id": cls.contract.id,
            # "product_id": cls.product_1.id,
            "name": "Services from #START# to #END#",
            "quantity": 1,
            # "uom_id": cls.product_1.uom_id.id,
            "price_unit": 100,
            "discount": 50,
            "recurring_rule_type": "monthly",
            "recurring_interval": 1,
            "date_start": "2020-01-01",
            "recurring_next_date": "2020-01-15",
        }
        with Form(cls.contract) as contract_form, freeze_time(contract_date):
            contract_form.contract_template_id = cls.template
            with contract_form.contract_line_ids.new() as line_form:
                line_form.product_id = cls.product_1
                line_form.name = "Services from #START# to #END#"
                line_form.quantity = 1
                line_form.price_unit = 100.0
                line_form.discount = 50
                line_form.recurring_rule_type = "monthly"
                line_form.recurring_interval = 1
                line_form.date_start = "2020-01-15"
                line_form.recurring_next_date = "2020-01-15"
        cls.contract_line = cls.contract.contract_line_ids[1]

        cls.contract2 = cls.env["contract.contract"].create(
            {
                "name": "Test Contract 2",
                "generation_type": "sale",
                "partner_id": cls.partner.id,
                "pricelist_id": cls.partner.property_product_pricelist.id,
                "contract_type": "purchase",
                "contract_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_1.id,
                            "name": "Services from #START# to #END#",
                            "quantity": 1,
                            "uom_id": cls.product_1.uom_id.id,
                            "price_unit": 100,
                            "discount": 50,
                            "recurring_rule_type": "monthly",
                            "recurring_interval": 1,
                            "date_start": "2018-02-15",
                            "recurring_next_date": "2018-02-22",
                        },
                    )
                ],
            }
        )

    def test_check_discount(self):
        with self.assertRaises(ValidationError):
            self.contract_line.write({"discount": 120})

    def test_contract(self):
        recurring_next_date = to_date("2020-02-15")
        self.assertAlmostEqual(self.contract_line.price_subtotal, 50.0)
        res = self.contract_line._onchange_product_id()
        self.assertIn("uom_id", res["domain"])
        self.contract_line.price_unit = 100.0
        self.contract.partner_id = self.partner.id
        self.contract.recurring_create_sale()
        self.sale_monthly = self.contract._get_related_sales()
        self.assertTrue(self.sale_monthly)
        self.assertEqual(self.contract_line.recurring_next_date, recurring_next_date)
        self.order_line = self.sale_monthly.order_line[0]
        self.assertTrue(self.order_line.tax_id)
        self.assertAlmostEqual(self.order_line.price_subtotal, 50.0)
        self.assertEqual(self.contract.user_id, self.sale_monthly.user_id)

    def test_contract_autoconfirm(self):
        recurring_next_date = to_date("2020-02-15")
        self.contract.sale_autoconfirm = True
        self.assertAlmostEqual(self.contract_line.price_subtotal, 50.0)
        res = self.contract_line._onchange_product_id()
        self.assertIn("uom_id", res["domain"])
        self.contract_line.price_unit = 100.0
        self.contract.partner_id = self.partner.id
        self.contract.recurring_create_sale()
        self.sale_monthly = self.contract._get_related_sales()
        self.assertTrue(self.sale_monthly)
        self.assertEqual(self.contract_line.recurring_next_date, recurring_next_date)
        self.order_line = self.sale_monthly.order_line[0]
        self.assertTrue(self.order_line.tax_id)
        self.assertAlmostEqual(self.order_line.price_subtotal, 50.0)
        self.assertEqual(self.contract.user_id, self.sale_monthly.user_id)

    def test_onchange_contract_template_id(self):
        """It should change the contract values to match the template."""
        self.contract.contract_template_id = False
        self.contract._onchange_contract_template_id()
        self.contract.contract_template_id = self.template
        self.contract._onchange_contract_template_id()
        res = {
            "contract_type": "sale",
            "contract_line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": self.product_1.id,
                        "name": "Test Contract Template",
                        "quantity": 1,
                        "uom_id": self.product_1.uom_id.id,
                        "price_unit": 100,
                        "discount": 50,
                        "recurring_rule_type": "yearly",
                        "recurring_interval": 1,
                    },
                )
            ],
        }
        del self.template_vals["name"]
        self.assertDictEqual(res, self.template_vals)

    def test_contract_count_sale(self):
        self.contract.recurring_create_sale()
        self.contract.recurring_create_sale()
        self.contract.recurring_create_sale()
        self.contract._compute_sale_count()
        self.assertEqual(self.contract.sale_count, 3)

    def test_contract_count_sale_2(self):
        orders = self.env["sale.order"]
        orders |= self.contract.recurring_create_sale()
        orders |= self.contract.recurring_create_sale()
        orders |= self.contract.recurring_create_sale()
        action = self.contract.action_show_sales()
        self.assertEqual(set(action["domain"][0][2]), set(orders.ids))

    def test_cron_recurring_create_sale(self):
        self.contract_line.date_start = "2020-01-01"
        self.contract_line.recurring_invoicing_type = "post-paid"
        self.contract_line.date_end = "2020-03-15"
        self.contract_line._onchange_is_auto_renew()
        contracts = self.contract2
        for _i in range(10):
            contracts |= self.contract.copy({"generation_type": "sale"})
        self.env["contract.contract"]._cron_recurring_create(create_type="sale")
        order_lines = self.env["sale.order.line"].search(
            [("contract_line_id", "in", contracts.mapped("contract_line_ids").ids)]
        )
        self.assertEqual(
            len(contracts.mapped("contract_line_ids")),
            len(order_lines),
        )

    def test_contract_sale_analytic(self):
        orders = self.env["sale.order"].browse()
        orders |= self.contract.recurring_create_sale()
        self.assertEqual(self.analytic_account, orders.mapped("analytic_account_id"))
