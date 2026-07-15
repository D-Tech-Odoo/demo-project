from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    brand_id = fields.Many2one(
        'product.brand',
        string='Brand',
        ondelete='set null'
    )

    model_number = fields.Char(string="Model Number")


    @api.model_create_multi
    def create(self, vals):
        products = super().create(vals)
        for product in products:
            if not product.default_code:
                product._generate_internal_reference()

        return products

    def _generate_internal_reference(self):
        for product in self:
            category = product.categ_id
            if not category.short_code:
                raise ValidationError(
                    _("Please define Short Code for the selected Product Category.")
                )

            sequence = self.env['ir.sequence'].next_by_code(
                'product.internal.reference'
            )

            brand_code = product.brand_id.code if product.brand_id else ''

            internal_ref = f"{category.short_code}-{brand_code}-{sequence}"

            # Handle blank brand formatting
            if not brand_code:
                internal_ref = f"{category.short_code}-{sequence}"

            product.default_code = internal_ref