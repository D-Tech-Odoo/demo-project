from odoo import models, fields, api, _
from odoo.exceptions import UserError
from lxml import etree
from markupsafe import Markup


class ProductCategory(models.Model):
    # _inherit = ['product.category', 'mail.thread', 'mail.activity.mixin']
    _name = 'product.category'  # optional but safe in this case
    _inherit = ['product.category', 'mail.thread', 'mail.activity.mixin']

    short_code = fields.Char(
        string="Short Code"
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('waiting_approval', 'Waiting for Approval'),
            ('approved', 'Approved'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        copy=False,
    )

    fields_readonly = fields.Boolean(
        compute='_compute_fields_readonly',
        store=False
    )

    # This field changes when group membership changes — used to bust compute cache
    user_has_approval_right = fields.Boolean(
        compute='_compute_user_has_approval_right',
        store=False,
    )

    def _compute_user_has_approval_right(self):
        has_right = self.env.user.has_group(
            'dtech_inventory_modification.group_product_category_approve_advnta'
        )
        for rec in self:
            rec.user_has_approval_right = has_right

    @api.depends('state', 'user_has_approval_right')
    def _compute_fields_readonly(self):
        for rec in self:
            if rec.user_has_approval_right:
                rec.fields_readonly = False
            else:
                rec.fields_readonly = rec.state in ('waiting_approval', 'approved')

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)

        if view_type == 'form':
            # Readonly when: user has NO approval right AND state is not draft
            lock_expr = "not user_has_approval_right and state != 'draft'"

            for node in arch.xpath("//field"):
                existing = node.get('readonly', '').strip()

                if existing and existing not in ('0', 'False', 'false'):
                    node.set('readonly', f"({lock_expr}) or ({existing})")
                else:
                    node.set('readonly', lock_expr)

        return arch, view

    def _user_has_approval_right(self):
        return self.env.user.has_group(
            'dtech_inventory_modification.group_product_category_approve_advnta'
        )

    def action_submit_for_approval(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Only Draft categories can be submitted for approval."))
            record.state = 'waiting_approval'

    def action_approve(self):
        for record in self:
            if record.state not in ('draft', 'waiting_approval'):
                raise UserError(_("Only Draft or Waiting for Approval categories can be approved."))
            if not self._user_has_approval_right():
                raise UserError(_("You do not have the right to approve product categories."))
            record.state = 'approved'
            record.message_post(
                body=Markup("<b>Approved by:</b> %s (ID: %s)") % (
                    self.env.user.name,
                    self.env.user.id,
                ),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )

    def action_reject(self):
        self.ensure_one()
        if not self._user_has_approval_right():
            raise UserError(_("You do not have the right to reject product categories."))
        if self.state != 'approved':
            raise UserError(_("Only Approved categories can be rejected."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Product Category'),
            'res_model': 'product.category.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_category_id': self.id},
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['state'] = 'draft'
        return super().create(vals_list)
