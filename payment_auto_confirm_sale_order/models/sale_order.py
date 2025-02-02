# © 2021 - today Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.multi
    def _create_payment_transaction(self, vals):
        transaction = super()._create_payment_transaction(vals)

        action = transaction.acquirer_id.auto_confirm_sale_order

        if action == "confirm_order":
            self.with_context(send_email=True).action_confirm()

        elif action == "send_quotation":
            self.force_quotation_send()

        return transaction
