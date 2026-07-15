from odoo import fields, models


class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    preferred_supplier = fields.Boolean(string="Preferred Supplier", default=False)