from odoo import models, fields, api

class ResDriver(models.Model):
    _name = 'res.driver'
    _description = 'Custom Driver Partner'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    street1 = fields.Char(string='Street 1')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    state = fields.Char(string='State')
    zip = fields.Char(string='Street 2')
    country_id = fields.Many2one('res.country', string='Country')
    complete_address = fields.Char(
        string='Address',
        compute='_compute_complete_address',
        store=True,
    )

    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')
    email = fields.Char(string='Email')

    @api.depends('street1', 'street2', 'city', 'state', 'zip', 'country_id')
    def _compute_complete_address(self):
        for rec in self:
            parts = [
                rec.street1,
                rec.street2,
                rec.city,
                rec.state,
                rec.zip,
                rec.country_id.name if rec.country_id else False,
            ]
            rec.complete_address = ', '.join(filter(None, parts))


