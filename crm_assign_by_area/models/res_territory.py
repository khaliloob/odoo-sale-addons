# © 2020 - today Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResTerritory(models.Model):
    _inherit = "res.territory"

    salesperson_id = fields.Many2one(
        comodel_name="res.users",
        string="Salesperson",
        track_visibility="onchange",
    )
