from odoo import fields, models

class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    common_return_reason = fields.Text(string='Common Return Reason')

    def action_create_returns(self):
        # Read reasons before super() clears transient records
        line_reasons = {
            line.move_id.id: line.line_return_reason
            for line in self.product_return_moves
        }

        result = super().action_create_returns()

        new_picking = self.env['stock.picking'].browse(result['res_id'])
        new_picking.common_return_reason = self.common_return_reason

        for move in new_picking.move_ids:
            origin_id = move.origin_returned_move_id.id
            if origin_id and origin_id in line_reasons and line_reasons[origin_id]:
                move.write({'line_return_reason': line_reasons[origin_id]})

        return result