from odoo import models, fields, api

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    use_expiration_date = fields.Boolean(
        string='Expiry Date',
        default=False,
        help="If enabled, an expiry date field will appear on all "
             "transfers of this operation type."
    )

    @api.onchange('use_expiration_date')
    def _onchange_use_expiration_date(self):
        if not self.use_expiration_date:
            # Clear expiry date on all related pickings when disabled
            self.env['stock.picking'].search([
                ('picking_type_id', '=', self._origin.id)
            ]).write({'expiry_date': False})