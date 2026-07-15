from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ReplacementRequest(models.Model):
    _name = "replacement.request"
    _description = "Replacement Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Replacement No",
        default=lambda self: _("New"),
        copy=False,
        readonly=True,
    )

    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
    )

    replacement_type = fields.Selection([
        ('warranty', 'Warranty'),
        ('doa', 'DOA'),
        ('foc', 'FOC'),
        ('chargeable', 'Chargeable'),
        ('upgrade', 'Upgrade'),
    ], default='warranty', required=True)

    reason = fields.Text()

    approved_by = fields.Many2one(
        "res.users",
        readonly=True,
    )

    approval_date = fields.Datetime(readonly=True)

    delivery_id = fields.Many2one(
        "stock.picking",
        readonly=True,
    )

    line_ids = fields.One2many(
        "replacement.request.line",
        "request_id",
        string="Products",
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('delivered', 'Delivered'),
        ('cancel', 'Cancelled'),
    ], compute="_compute_state", store=True, readonly=False)

    @api.depends("delivery_id", "delivery_id.state")
    def _compute_state(self):
        for rec in self:
            if rec.delivery_id:
                if rec.delivery_id.state == "done":
                    rec.state = "delivered"
                elif rec.delivery_id.state == "cancel":
                    rec.state = "cancel"
                else:
                    rec.state = "approved"
            else:
                if not rec.state or rec.state == "approved":
                    rec.state = "draft"

    @api.model
    def create(self, vals_list):
        if vals_list.get("name", _("New")) == _("New"):
            vals_list["name"] = self.env["ir.sequence"].next_by_code(
                "replacement.request"
            ) or _("New")
        return super().create(vals_list)

    def action_approve(self):
        for rec in self:

            if rec.delivery_id:
                raise UserError(_("Delivery already created."))

            rec.approved_by = self.env.user
            rec.approval_date = fields.Datetime.now()

            picking = rec._create_delivery()

            rec.write({
                "delivery_id": picking.id,
                "state": "approved",
            })

    def action_cancel(self):
        self.state = "cancel"

    def action_reset(self):
        self.state = "draft"
        self.delivery_id = False

    def action_view_delivery(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Delivery",
            "res_model": "stock.picking",
            "view_mode": "form",
            "res_id": self.delivery_id.id,
        }

    def _create_delivery(self):
        warehouse = self.env["stock.warehouse"].search([], limit=1)
        picking_type = warehouse.out_type_id

        picking = self.env["stock.picking"].create({
            "partner_id": self.customer_id.id,
            "picking_type_id": picking_type.id,
            "location_id": picking_type.default_location_src_id.id,
            "location_dest_id": self.customer_id.property_stock_customer.id,
            "origin": self.name,
        })

        for line in self.line_ids:
            self.env["stock.move"].create({
                "name": line.replacement_product_id.display_name,
                "product_id": line.replacement_product_id.id,
                "product_uom_qty": line.replacement_product_qty,
                "product_uom": line.replacement_product_uom.id,
                "location_id": picking.location_id.id,
                "location_dest_id": picking.location_dest_id.id,
                "picking_id": picking.id,
            })

        return picking




class ReplacementRequestLine(models.Model):
    _name = "replacement.request.line"
    _description = "Replacement Request Line"

    request_id = fields.Many2one(
        "replacement.request",
        required=True,
        ondelete="cascade",
    )

    # Returned Product

    original_product_id = fields.Many2one(
        "product.product",
        string="Original Product",
        required=True,
    )

    returned_serial_id = fields.Many2one(
        "stock.lot",
        string="Returned Serial",
        domain="[('product_id','=',original_product_id)]",
    )

    original_product_qty = fields.Float(
        string="Qty",
        default=1,
        required=True,
    )

    original_product_uom = fields.Many2one(
        "uom.uom",
        string="UoM",
        related="original_product_id.uom_id",
        store=True,
        readonly=True,
    )

    # Replacement Product

    replacement_product_id = fields.Many2one(
        "product.product",
        string="Replacement Product",
        required=True,
    )

    replacement_serial_id = fields.Many2one(
        "stock.lot",
        string="Replacement Serial",
        domain="[('product_id','=',replacement_product_id)]",
    )

    replacement_product_qty = fields.Float(
        string="Qty",
        default=1,
        required=True,
    )

    replacement_product_uom = fields.Many2one(
        "uom.uom",
        string="UoM",
        related="replacement_product_id.uom_id",
        store=True,
        readonly=True,
    )