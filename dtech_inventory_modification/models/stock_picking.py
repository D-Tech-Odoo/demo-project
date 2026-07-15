from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    approval_sent = fields.Boolean(string="Approval Sent", default=False)

    is_return = fields.Boolean(
        string="Is Return",
        compute="_compute_is_return",
        store=True
    )

    is_internal = fields.Boolean(
        string="Is Internal Transfer",
        compute="_compute_is_internal",
    )

    is_admin = fields.Boolean(compute="_compute_is_admin")
    is_user = fields.Boolean(compute="_compute_is_user")
    exceed_admin = fields.Boolean(compute="_compute_is_exceed_admin")

    awb_no = fields.Char(string="AWB Number")
    bl_no = fields.Char(string="BL Number")
    container_no = fields.Char(string="Container Number")
    curier_track_no = fields.Char(string="Courier Tracking Number")


    common_return_reason = fields.Text(string="Return Reason")

    invoice_count = fields.Integer(compute="_compute_invoice_count", string="Invoices")

    driver_id = fields.Many2one('res.driver', string="Driver")
    carrier = fields.Char(string="Carrier")
    driver_no = fields.Char(
        string="Driver No.",
        compute='_compute_driver_no',
        store=True,
        readonly=True,
    )

    eta_date = fields.Date(string="ETA")


    # Flag relayed from operation type — drives visibility in the view
    picking_type_use_expiration_date = fields.Boolean(
        related='picking_type_id.use_expiration_date',
        string='Use Expiry Date',
        store=False,
    )

    # The actual date field the user fills in
    expiry_date = fields.Date(
        string='Expiry Date',
    )

    is_foreign_po = fields.Boolean(
        compute="_compute_is_foreign_po",
        store=True,
    )
    is_exceed = fields.Boolean(string='Is Exceed', default=False)


    state = fields.Selection(
        selection_add=[
            ('waiting_approval', 'Waiting For Approval'),
            ('supplier_dispatch', 'Supplier Dispatch'),
            ('freight_forwarder', 'Freight Forwarder Handover'),
            ('arrived_port', 'Arrived to Sri Lankan Ports'),
            ('customs', 'Customs Clearance'),
            ('warehouse_arrival', 'Warehouse Arrival'),
            ('exceed_po', 'Exceed PO QTY'),
            ('delivered', 'Delivered To Customer'),
        ],
    )
    remarks = fields.Text(string="Remarks")

    def action_delivered_customer(self):
        self.write({'state': 'delivered'})

    def action_print_dn(self):
        self.ensure_one()
        return self.env.ref(
            "dtech_inventory_modification.action_delivery_note_pdf"
        ).report_action(self, config=False)

    @api.depends('driver_id.phone', 'driver_id.mobile')
    def _compute_driver_no(self):
        for rec in self:
            rec.driver_no = rec.driver_id.phone or rec.driver_id.mobile or False

    @api.depends('purchase_id.supplier_origin')
    def _compute_is_foreign_po(self):
        for picking in self:
            picking.is_foreign_po = (
                    picking.purchase_id.supplier_origin == 'foreign'
            )

    def action_exceed_po(self):
        self.write({'state': 'waiting_approval'})

    def action_supplier_dispatch(self):
        self.write({'state': 'supplier_dispatch'})

    def action_freight_forwarder(self):
        self.write({'state': 'freight_forwarder'})

    def action_arrived_port(self):
        self.write({'state': 'arrived_port'})

    def action_customs(self):
        self.write({'state': 'customs'})

    def action_warehouse_arrival(self):
        self.write({'state': 'warehouse_arrival'})

    def _compute_invoice_count(self):
        for picking in self:
            picking.invoice_count = self.env['account.move'].search_count([
                ('picking_id', '=', picking.id)
            ])

    def action_view_invoices(self):
        """Open all invoices/credit notes linked to this picking."""
        self.ensure_one()

        invoices = self.env['account.move'].search([
            ('picking_id', '=', self.id)
        ])

        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        action['domain'] = [('id', 'in', invoices.ids)]

        # Open form directly when only one invoice
        if len(invoices) == 1:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = invoices.id

        return action

    # only for sale order delivery returns
    @api.depends('move_ids.origin_returned_move_id',
                 'move_ids.origin_returned_move_id.picking_id.picking_type_code')
    def _compute_is_return(self):
        for rec in self:
            is_sale_return = False
            for move in rec.move_ids:
                origin_picking = move.origin_returned_move_id.picking_id
                if (
                        origin_picking
                        and origin_picking.picking_type_code == 'outgoing'
                        and origin_picking.sale_id
                ):
                    is_sale_return = True
                    break
            rec.is_return = is_sale_return

    # @api.depends('move_ids.origin_returned_move_id')
    # def _compute_is_return(self):
    #     for rec in self:
    #         rec.is_return = any(move.origin_returned_move_id for move in rec.move_ids)

    def _compute_is_internal(self):
        for rec in self:
            rec.is_internal = rec.picking_type_id.code == 'internal'


    def _compute_is_exceed_admin(self):
        for rec in self:
            rec.exceed_admin = self.env.user.has_group(
                'dtech_inventory_modification.group_exceed_qty_approver'
            )

    def _compute_is_admin(self):
        for rec in self:
            rec.is_admin = self.env.user.has_group(
                'dtech_inventory_modification.group_return_admin_custom'
            )

    def _compute_is_user(self):
        for rec in self:
            rec.is_user = self.env.user.has_group(
                'dtech_inventory_modification.group_return_user_custom'
            )



    def action_send_to_approve(self):
        for rec in self:
            rec.state = 'waiting_approval'
            rec.approval_sent = True

    def button_validate(self):
        for rec in self:
            if rec.state == 'waiting_approval':
                if not self.env.user.has_group(
                        'dtech_inventory_modification.group_return_admin_custom'):
                    raise AccessError(
                        _("Only Admin can approve this return.")
                    )

                # Extra safety: block non-admins from directly validating internal transfers
                if rec.state == 'assigned' and rec.is_internal:
                    if not self.env.user.has_group(
                            'dtech_inventory_modification.group_return_admin_custom'):
                        raise AccessError(
                            _("Only Admin can validate internal transfers.")
                        )

        return super().button_validate()



        for rec in self:
            if rec.origin and rec.origin.startswith("Return of") and rec.state == 'done':
                return rec._action_open_credit_note()

        return result

    def _action_open_credit_note(self):
        """Open a new credit note with the returned products from the picking."""
        line_vals = []

        for move in self.move_ids_without_package:
            line_vals.append((0, 0, {
                'product_id': move.product_id.id,
                'quantity': move.quantity,
                'price_unit': move.product_id.list_price,  # or 0 if you want
                'name': move.product_id.display_name,
            }))

        return {
            'name': 'Create Credit Note',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'context': {
                'default_move_type': 'out_refund',  # customer credit note
                'default_partner_id': self.partner_id.id,
                'default_invoice_line_ids': line_vals,
                'default_invoice_origin': self.origin,
                'default_ref': self.name + " Return",
                'default_picking_id': self.id,
            },
            'target': 'current',
        }

    def action_cancel(self):
        for picking in self:
            if picking.backorder_id and not self.env.user.has_group(
                    "dtech_inventory_modification.group_backorder_cancel_approval"
            ):
                raise UserError(_(
                    "You are not allowed to cancel a backorder."
                ))

        return super().action_cancel()

class AccountMove(models.Model):
    _inherit = 'account.move'

    picking_id = fields.Many2one('stock.picking', string="Picking")