from odoo import models, fields

class StockCountNotificationDays(models.Model):
    _name = 'stock.count.notification.days'
    _description = 'Stock Count Notification Days'

    name = fields.Char(string="Description")
    days = fields.Integer(string="Days Before")