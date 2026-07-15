from odoo import models, api, _
import logging

_logger = logging.getLogger(__name__)


class StockWarehouseOrderpoint(models.Model):
    _name = 'stock.warehouse.orderpoint'
    _inherit = ['stock.warehouse.orderpoint', 'mail.thread', 'mail.activity.mixin']

    @api.model
    def check_minimum_stock_and_notify(self):
        template = self.env.ref(
            'dtech_inventory_modification.email_template_min_stock',
            raise_if_not_found=False
        )
        if not template:
            _logger.warning("Minimum stock alert email template not found!")
            return

        purchasing_employees = self.env['hr.employee'].search([
            ('department_id.name', 'ilike', 'Purchasing'),
            ('work_email', '!=', False),
        ])

        if not purchasing_employees:
            _logger.warning("No employees found in Purchasing department.")
            return

        purchasing_emails = ','.join(
            emp.work_email for emp in purchasing_employees if emp.work_email
        )

        purchasing_partners = purchasing_employees.mapped('user_id.partner_id').filtered('id')

        for orderpoint in self.search([]):

            on_hand_qty = orderpoint.qty_on_hand

            if on_hand_qty <= orderpoint.product_min_qty:
                try:
                    template.send_mail(
                        orderpoint.id,
                        force_send=True,
                        email_values={
                            'email_to': purchasing_emails,
                            'partner_ids': [(6, 0, purchasing_partners.ids)],
                        }
                    )

                    recipient_names = ', '.join(purchasing_employees.mapped('name'))
                    orderpoint.product_id.product_tmpl_id.message_post(
                        body=_(
                            "<b>Minimum Stock Alert sent</b><br/>"
                            "Product: <b>%s</b><br/>"
                            "On Hand Qty: <b>%s</b><br/>"
                            "Minimum Qty: <b>%s</b><br/>"
                            "Location: <b>%s</b><br/>"
                            "Email sent to: %s"
                        ) % (
                                 orderpoint.product_id.name,
                                 on_hand_qty,
                                 orderpoint.product_min_qty,
                                 orderpoint.location_id.complete_name,
                                 recipient_names,
                             ),
                        subtype_xmlid='mail.mt_note',
                    )

                    _logger.info(
                        "Minimum stock alert sent for product '%s' | On Hand: %s | Min Qty: %s | Recipients: %s",
                        orderpoint.product_id.name, on_hand_qty, orderpoint.product_min_qty, purchasing_emails
                    )

                except Exception as e:
                    _logger.error(
                        "Failed to send minimum stock alert for product '%s': %s",
                        orderpoint.product_id.name, str(e)
                    )