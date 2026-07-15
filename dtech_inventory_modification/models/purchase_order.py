from odoo import fields, models

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    supplier_origin = fields.Selection([
        ('local','Local'),
        ('foreign','Foreign'),
    ], string="Supplier Origin", default='local')


