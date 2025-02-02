# © 2020 - today Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from collections import defaultdict
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    is_kit = fields.Boolean()
    kit_sequence = fields.Integer()
    is_kit_component = fields.Boolean()
    is_important_kit_component = fields.Boolean()
    kit_reference = fields.Char()
    kit_reference_readonly = fields.Boolean()
    kit_initialized = fields.Boolean()
    available_kit_references = fields.Char(related="order_id.available_kit_references")
    next_kit_reference = fields.Char(related="order_id.next_kit_reference")
    qty_delivered_method = fields.Selection(selection_add=[("kit", "Kit")])
    kit_previous_quantity = fields.Float(
        digits=dp.get_precision("Product Unit of Measure")
    )

    kit_line_ids = fields.One2many(
        "sale.order.line", "kit_id", "Components", readonly=True, copy=False
    )
    kit_id = fields.Many2one(
        "sale.order.line", "Kit", store=True, compute="_compute_kit_id", copy=False
    )

    @api.onchange("product_id")
    def product_id_change(self):
        res = super().product_id_change()
        self.is_kit = self.product_id.is_kit
        return res

    @api.onchange("product_uom", "product_uom_qty")
    def product_uom_change(self):
        super().product_uom_change()

        if self.is_kit:
            self.price_unit = 0

    def initialize_kit(self):
        self.kit_reference = self.next_kit_reference
        self.kit_previous_quantity = self.product_uom_qty
        self.add_kit_components()
        self.set_kit_line_readonly_conditions()
        self.kit_initialized = True

    def set_kit_line_readonly_conditions(self):
        self.handle_widget_invisible = False
        self.trash_widget_invisible = False
        self.product_readonly = True
        self.product_uom_qty_readonly = False
        self.product_uom_readonly = True
        self.kit_reference_readonly = True

    def add_kit_components(self):
        for kit_line in self.product_id.kit_line_ids:
            component_line = self.prepare_kit_component(kit_line)
            self.order_id.order_line |= component_line

    def prepare_kit_component(self, kit_line):
        new_line = self.new({})
        new_line.kit_reference = self.kit_reference
        new_line.is_kit_component = True
        new_line.is_important_kit_component = kit_line.is_important
        self._set_kit_component_display_type(new_line, kit_line)
        self._set_kit_component_product_and_quantity(new_line, kit_line)
        self._set_kit_component_readonly_conditions(new_line, kit_line)
        self._set_kit_component_name(new_line, kit_line)
        self._set_kit_component_discount(new_line)
        return new_line

    def _set_kit_component_display_type(self, new_line, kit_line):
        new_line.display_type = kit_line.display_type

    def _set_kit_component_product_and_quantity(self, new_line, kit_line):
        new_line.set_product_and_quantity(
            order=self.order_id,
            product=kit_line.component_id,
            uom=kit_line.uom_id,
            qty=kit_line.quantity,
        )

    def _set_kit_component_name(self, new_line, kit_line):
        if kit_line.name:
            new_line.name = kit_line.name

    def _set_kit_component_discount(self, new_line):
        discount = self.product_id.kit_discount
        if discount:
            new_line.discount = discount * 100

    def set_product_and_quantity(self, order, product, uom, qty):
        self.product_id = product
        self.order_id = order
        self.product_id_change()

        self.product_uom = uom
        self.product_uom_qty = qty
        self.product_uom_change()

    def _set_kit_component_readonly_conditions(self, new_line, kit_line):
        is_important = kit_line.is_important
        new_line.handle_widget_invisible = False
        new_line.trash_widget_invisible = is_important
        new_line.product_readonly = is_important
        new_line.product_uom_qty_readonly = is_important
        new_line.product_uom_readonly = is_important
        new_line.kit_reference_readonly = is_important

    def _update_kit_component_quantities(self):
        factor = self._get_kit_components_quantity_factor()

        if factor != 1:
            self._apply_kit_components_quantity_factor(factor)

        self.kit_previous_quantity = self.product_uom_qty

    def _get_kit_components_quantity_factor(self):
        return (
            self.product_uom_qty / self.kit_previous_quantity
            if self.kit_previous_quantity
            else 1
        )

    def _apply_kit_components_quantity_factor(self, factor):
        for line in self._get_kit_component_lines():
            line.product_uom_qty *= factor
            line.product_uom_change()

    def recompute_sequences(self):
        next_sequence = 1
        for line in self:
            line.sequence = next_sequence
            next_sequence += 1

    def recompute_kit_sequences(self, kits):
        kit_sequences = {l.kit_reference: l.sequence for l in kits}
        next_sequences = defaultdict(lambda: 1)

        for line in self:
            kit_ref = line.kit_reference
            line.sequence = kit_sequences.get(kit_ref)
            line.kit_sequence = next_sequences[kit_ref]
            next_sequences[kit_ref] += 1

    def sorted_by_sequence(self):
        return self.sorted(key=lambda l: l.sequence)

    def sorted_by_kit_sequence(self):
        return self.sorted(key=lambda l: l.kit_sequence)

    def _get_kit_line(self):
        if self.is_kit or not self.kit_reference:
            return None

        return self.order_id.order_line.filtered(
            lambda l: l.is_kit and l.kit_reference == self.kit_reference
        )[0:1]

    def _get_kit_component_lines(self):
        return self.order_id.order_line.filtered(
            lambda l: not l.is_kit and l.kit_reference == self.kit_reference
        )

    @api.depends("kit_reference")
    def _compute_kit_id(self):
        for line in self:
            line.kit_id = line._get_kit_line()

    @api.depends("is_kit")
    def _compute_qty_delivered_method(self):
        super()._compute_qty_delivered_method()
        kits = self.filtered(
            lambda l: l.is_kit and l.product_id.type not in ("product", "consu")
        )
        kits.update({"qty_delivered_method": "kit"})

    @api.depends("product_uom_qty", "kit_line_ids", "kit_line_ids.qty_delivered")
    def _compute_qty_delivered(self):
        super()._compute_qty_delivered()
        kit_lines = self.filtered(lambda l: l.qty_delivered_method == "kit")
        kit_lines._compute_kit_qty_delivered()

    def _compute_kit_qty_delivered(self):
        for line in self:
            line.qty_delivered = line._get_kit_qty_delivered()

    def _get_kit_qty_delivered(self):
        ratio = self._get_kit_qty_delivered_ratio()
        return ratio * self.product_uom_qty

    def _get_kit_qty_delivered_ratio(self):
        component = self._get_first_important_component()

        if component.product_uom_qty:
            return component.qty_delivered / component.product_uom_qty
        elif component.qty_delivered:
            return 1
        else:
            return 0

    def _get_first_important_component(self):
        return self.kit_line_ids.filtered("is_important_kit_component")[:1]
