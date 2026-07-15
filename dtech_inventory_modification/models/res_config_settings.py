from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_product_category_approve_advnta = fields.Boolean(
        string='Product Category Creation',
        implied_group='dtech_inventory_modification.group_product_category_approve_advnta',
        help="Users with this right can approve or reject product categories directly. Others must submit for approval.",
    )