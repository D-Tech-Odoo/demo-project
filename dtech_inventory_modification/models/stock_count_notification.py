from odoo import models, fields, api
from datetime import timedelta, date

class StockCountNotification(models.Model):
    _name = 'stock.count.notification'
    _description = 'Stock Count Notification'
    _rec_name = 'id'

    # name = fields.Char(string="Reference")

    count_date = fields.Date(string="Stock Count Date", required=True)

    # before_days = fields.Selection([
    #     ('1', '1 Day Before'),
    #     ('3', '3 Days Before'),
    #     ('5', '5 Days Before'),
    #     ('7', '7 Days Before'),
    # ], string="Before No of Days", required=True)

    before_day_id = fields.Many2one(
        'stock.count.notification.days',
        string="Before No of Days",
        required=True
    )

    user_ids = fields.Many2many(
        'res.users',
        string="Users"
    )

    email_template_id = fields.Many2one(
        'mail.template',
        string="Email Template"
    )

    def check_stock_notifications(self):
        today = fields.Date.today()
        records = self.search([])
        for rec in records:
            before_days = rec.before_day_id.days
            notify_date = rec.count_date - timedelta(days=before_days)
            if notify_date == today:
                for user in rec.user_ids:
                    rec.email_template_id.send_mail(
                        rec.id,
                        email_values={'email_to': user.email},
                        force_send=True
                    )

    # def check_stock_notifications(self):
    #
    #     today = fields.Date.today()
    #
    #     records = self.search([])
    #
    #     for rec in records:
    #         before = int(rec.before_days)
    #         notify_date = rec.count_date - timedelta(days=before)
    #         if notify_date == today:
    #             if rec.email_template_id:
    #                 for user in rec.user_ids:
    #                     rec.email_template_id.send_mail(
    #                         rec.id,
    #                         email_values={
    #                             'email_to': user.email
    #                         },
    #                         force_send=True
    #                     )