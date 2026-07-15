from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare

class StockMove(models.Model):
    _inherit = 'stock.move'

    line_return_reason = fields.Text(string="Line Return Reason")
    remark = fields.Char(string="Remark")

    @api.constrains('quantity')
    def _check_po_qty_vs_done(self):
        for move in self:

            if move.picking_id.picking_type_code != 'incoming':
                continue

            if not move.purchase_line_id:
                continue

            # Convert PO qty into product UoM (VERY IMPORTANT)
            po_qty_converted = move.purchase_line_id.product_uom._compute_quantity(
                move.purchase_line_id.product_qty,
                move.product_uom
            )

            # Sum all related moves (same PO line)
            related_moves = move.picking_id.move_ids.filtered(
                lambda m: m.purchase_line_id == move.purchase_line_id
            )
            total_move_qty = sum(related_moves.mapped('quantity'))

            precision = move.product_uom.rounding

            # Compare in SAME UoM
            if float_compare(
                    total_move_qty,
                    po_qty_converted,
                    precision_rounding=precision
            ) == 1:

                move.picking_id.is_exceed = True
                move.picking_id.state = 'exceed_po'

                # Ignore tiny float diff
                if abs(total_move_qty - po_qty_converted) < precision:
                    continue

                # raise ValidationError(
                #     _("Received quantity cannot exceed PO quantity for product: %s")
                #     % move.product_id.display_name
                # )



