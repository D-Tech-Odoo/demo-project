from odoo import fields, models

class StockReturnPickingLine(models.TransientModel):
    _inherit = 'stock.return.picking.line'

    reason = fields.Many2one('stock.picking.return.reason', string='Reason')
    description = fields.Char(string='Description')
    line_return_reason = fields.Text(string='Line Return Reason')