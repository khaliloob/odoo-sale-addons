# © 2021 - today Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Purchase Sale Inter Company Route",
    "version": "1.0.0",
    "author": "Numigi",
    "maintainer": "Numigi",
    "website": "https://bit.ly/numigi-com",
    "license": "LGPL-3",
    "category": "Sales",
    "summary": "Allow to rent equipments",
    "depends": [
        "purchase_sale_inter_company",
        "sale_order_global_stock_route",
        "sale_stock",
    ],
    "data": ["data/stock_picking_type.xml", "data/stock_route.xml"],
    "installable": True,
    "post_init_hook": "post_init_hook",
}
