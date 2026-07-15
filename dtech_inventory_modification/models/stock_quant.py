from odoo import models, fields, api

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    adjustment_reason = fields.Char(
        string="Reference",
        compute='_compute_adjustment_reason',
        store=False 
    )

    def _compute_adjustment_reason(self):
        for quant in self:
            move_line = self.env['stock.move.line'].search([
                ('product_id', '=', quant.product_id.id),
                '|',
                ('location_id', '=', quant.location_id.id),
                ('location_dest_id', '=', quant.location_id.id)
            ], order='date desc', limit=1)
            quant.adjustment_reason = move_line.reference if move_line else False