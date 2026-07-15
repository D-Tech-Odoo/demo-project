from odoo import models, fields, api, _
from odoo.exceptions import UserError
from markupsafe import Markup


class ProductCategoryRejectWizard(models.TransientModel):
    _name = 'product.category.reject.wizard'
    _description = 'Product Category Rejection Wizard'

    category_id = fields.Many2one(
        'product.category',
        string='Product Category',
        required=True,
        readonly=True,
    )
    reason = fields.Text(
        string='Rejection Reason',
        required=True,
    )

    def action_confirm_reject(self):
        self.ensure_one()

        if not self.reason or not self.reason.strip():
            raise UserError(_("Please enter a rejection reason."))

        category = self.category_id

        body = _(
            "Rejected by: %(user)s<br/>"
            "Reason: %(reason)s",
            user=self.env.user.name,
            reason=self.reason,
        )
        category.message_post(
            body=Markup("<b>Rejected by:</b> %s (ID: %s)<br/><b>Reason:</b> %s") % (
                self.env.user.name,
                self.env.user.id,
                self.reason,
            ),
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )

        category.state = 'draft'

        return {'type': 'ir.actions.act_window_close'}