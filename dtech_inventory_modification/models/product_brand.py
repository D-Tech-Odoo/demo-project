from odoo import models, fields

class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Product Brand'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(string='Brand Name', required=True)
    code = fields.Char(string='Brand Code')
