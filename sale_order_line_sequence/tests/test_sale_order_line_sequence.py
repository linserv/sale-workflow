# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSaleOrderLineSequence(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_order = cls.env["sale.order"]
        cls.sale_order_line = cls.env["sale.order.line"]
        cls.account_move = cls.env["account.move"]
        cls.account_move_line = cls.env["account.move.line"]
        cls.partner = cls.env["res.partner"].create({
            "name": "Demo Partner",
            "is_company": True,
            "street": "1839 Arbor Way",
            "city": "Turlock",
            "state_id": cls.env.ref("base.state_us_5").id,
            "zip": "95380",
            "country_id": cls.env.ref("base.us").id,
            "email": "wood.corner26@example.com",
            "phone": "(623)-853-7197",
            "website": "http://www.wood-corner.com",
            "vat": "US12345672",
        })
        categ_id = cls.env["product.category"].create({
            "name": "Test Office Furniture",
            "parent_id": cls.env.ref("product.product_category_1").id
        })
        cls.product = cls.env["product.product"].create({
            "name": "Furniture Test",
            "default_code": "FURN_009601",
            "standard_price": 500.0,
            "weight": 0.01,
        })
        cls.product_2 = cls.env["product.product"].create({
            "name": "Conference Chair",
            "categ_id": categ_id.id,
            "standard_price": 28,
            "list_price": 33,
            "type": "consu",
            "uom_id": cls.env.ref("uom.product_uom_unit").id,
            "uom_po_id": cls.env.ref("uom.product_uom_unit").id,
        })

    def _create_sale_order(self):
        vals = {
            "partner_id": self.partner.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "name": self.product.name,
                        "product_id": self.product.id,
                        "product_uom_qty": 5.0,
                        "product_uom": self.product.uom_id.id,
                        "price_unit": 500.0,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "name": self.product_2.name,
                        "product_id": self.product_2.id,
                        "product_uom_qty": 5.0,
                        "product_uom": self.product.uom_id.id,
                        "price_unit": 150,
                    },
                ),
            ],
        }

        return self.sale_order.create(vals)

    def test_sale_order_line_sequence(self):
        so1 = self._create_sale_order()
        so1.action_confirm()
        self.assertEqual(so1.order_line[0].visible_sequence, 1)
        so2 = so1.copy()
        self.assertEqual(so2.order_line[0].visible_sequence, 1)

    def test_sale_order_line_sequence_section(self):
        so1 = self._create_sale_order()
        self.sale_order_line.create(
            {
                "name": "Note 1",
                "order_id": so1.id,
                "display_type": "line_section",
            }
        )
        self.sale_order_line.create(
            {
                "name": self.product_2.name,
                "order_id": so1.id,
                "product_id": self.product_2.id,
                "product_uom_qty": 3.0,
                "product_uom": self.product.uom_id.id,
                "price_unit": 200,
            }
        )
        so1.action_confirm()

        sequence = 1
        for line in so1.order_line:
            if line.display_type:
                self.assertFalse(line.visible_sequence)
                continue
            self.assertEqual(line.visible_sequence, sequence)
            sequence += 1

    def test_invoice_sequence(self):
        """
        Verify that the sequence is correctly assigned to the account move associated
        with the sale order line it references.
        """
        so = self._create_sale_order()
        so.action_confirm()
        so.order_line.qty_delivered = 5
        self.invoice = so._create_invoices()
        self.assertEqual(
            str(so.order_line[0].visible_sequence),
            self.invoice.line_ids[0].related_so_sequence,
        )
        self.assertEqual(
            str(so.order_line[1].visible_sequence),
            self.invoice.line_ids[1].related_so_sequence,
        )
