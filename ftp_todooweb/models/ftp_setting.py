# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import os

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date

try:
    import ftplib
except ImportError:
    raise ImportError('This module needs pysftp to automaticly write backups to the FTP through SFTP. Please install pysftp on your system. (sudo pip install pysftp)')

try:
    import urllib.request as urllib2
except ImportError:
    raise ImportError("This module needs urllib2. (sudo pip install urllib2)")

try:
    import ssl
except ImportError:
    ssl = None

import logging
_logger = logging.getLogger(__name__)


class FtpSetting(models.Model):
    _name = 'ftp.setting'
    _description = 'Settings'
    _rec_name = 'user'

    user = fields.Char('User', index=True, required=True)
    secret = fields.Char('Password', required=True, copy=False)
    url = fields.Char('Server', required=True)
    url_output = fields.Char('Output Url', help="Path on the server for outgoing files")
    url_server_output = fields.Char('Server Output', help="Path on the server for outgoing files")
    state = fields.Selection([
        ('no_connect', 'Not connected'),
        ('connect', 'Connected')
    ], string='Status server', index=True, default='no_connect', required=True)
    type_connection = fields.Selection([
        ('ftp', 'FTP'),
        # ('other', 'Other')
    ], string='Type conection', index=True, default='ftp', required=True)
    type_encrypt = fields.Selection([
        # ('tls', 'TLS'),
        ('other', 'SSL')
    ], string='Type Encrypt', index=True, default='other')
    active = fields.Boolean('Active')

    def test_connection(self):
        for obj_connect in self:
            status_code = False
            user = obj_connect.user
            secret = obj_connect.secret
            url = obj_connect.url
            ftp = None  # Initialize ftp outside the try block
            try:
                if obj_connect.type_encrypt == 'tls':
                    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
                    ftp = ftplib.FTP_TLS(host=url, context=context)
                    ftp.connect(url)
                    ftp.login(user, secret)  # Add login here
                    ftp.prot_p()
                else:
                    ftp = ftplib.FTP(url)  # Abre la sesión
                    ftp.login(user, secret)  # Add login here

                if ftp and ftp.welcome.count('220') > 0:
                    _logger.info("Connection successful at TEST!!")
                    obj_connect.write({'state': 'connect', 'active': True})
                    status_code = True
            except Exception as e:
                _logger.error(f"FTP Connection Error: {e}")  # More specific error message
                raise UserError(
                    _("Check your configuration, we can't connect,\n"
                      "Here is the error:\n%s") % e)
            finally:
                return status_code, ftp  # Return ftp object

    def test_connection00(self, obj_con):
        status_code = False
        ftp = None  # Initialize ftp outside the try block
        if obj_con:
            user = obj_con.user
            secret = obj_con.secret
            url = obj_con.url
            try:
                if obj_con.type_encrypt == 'tls':
                    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
                    ftp = ftplib.FTP_TLS(host=url, context=context)
                    ftp.connect(url)
                    ftp.login(user, secret)  # Add login here
                    ftp.prot_p()
                else:
                    ftp = ftplib.FTP(url)  # Abre la sesión
                    ftp.login(user, secret)  # Add login here

                if ftp and ftp.welcome.count('220') > 0:
                    _logger.info("Connection successful at CRON!!")
                    obj_con.write({'state': 'connect', 'active': True})
                    status_code = True
            except Exception as e:
                _logger.error(f"FTP Connection Error: {e}")  # More specific error message
                raise UserError(
                    _("Check your configuration, we can't connect,\n"
                      "Here is the error:\n%s") % e)
            finally:
                return status_code, ftp  # Return ftp object

    def upload(self, ftp, filename):
        part_fin = '.txt'
        try:
            with open(filename, "rb") as f:
                if filename.split('.')[-1:][0] in ['png', 'jpg', 'jpeg']:
                    part_fin = '.jpg'
                elif filename.split('.')[-1:][0] in ['csv']:
                    part_fin = '.csv'
                elif filename.split('.')[-1:][0] in ['xlsx', 'xls']:
                    part_fin = '.xls'
                elif filename.split('.')[-1:][0] in ['txt']:
                    part_fin = '.txt'
                elif filename.split('.')[-1:][0] in ['pdf']:
                    part_fin = '.pdf'
                elif filename.split('.')[-1:][0] in ['doc']:
                    part_fin = '.doc'
                file_name = filename.split('/')[-1].split('.')[:1][0]
                result_name = file_name + part_fin
                stor_name = "STOR " + str(result_name)
                ftp.storbinary(stor_name, f)
            f.close()
            return True
        except Exception as e:
            _logger.error(f"FTP Upload Error: {e}")
            return False  # Or raise an exception, depending on your error handling strategy


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    file_send_id = fields.Many2one('attachment.files.send', 'Attachmente Files', index=True)


class AttachmentFilesSend(models.Model):
    _name = 'attachment.files.send'
    _description = 'Attachment Files'
    _order = 'create_date desc'

    name = fields.Char('Document Name', default="New Attachments", index=True, required=True)
    attachment_ids = fields.One2many('ir.attachment', 'file_send_id', 'Attachments')
    state = fields.Selection([
        # por defecto
        ('draft', 'Draft'),
        # cuando se generan los doc
        ('pend', 'Pending sent'),
        # cuando el cron lo envia al ftp
        ('send', 'Send'),
    ], string='Status', index=True, defaulf='draft')
    ribbon_message = fields.Char('Ribbon message')

    @api.model
    def create(self, vals):
        request = super(AttachmentFilesSend, self).create(vals)
        if request.name == "New Attachments":
            sequence_name = self.env['ir.sequence'].next_by_code('attachment.files.send') or "New Attachments"
            request.name = 'FTP' + sequence_name
            request.state = 'draft'
        return request

    @api.depends('attachment_ids')
    @api.onchange('attachment_ids')
    def onchange_attachment_ids(self):
        for attach in self:
            if attach.attachment_ids:
                attach.state = 'pend'
            else:
                attach.state = 'draft'

    def sent_server(self):
        for obj_ftp in self:
            if obj_ftp.attachment_ids:
                files = obj_ftp.attachment_ids
                obj_connection_id = self.env['ftp.setting'].search([('active', '=', True)])
                if obj_connection_id:
                    obj_connect = obj_connection_id[0]
                    url_output = obj_connect.url_output
                    url_server_output = obj_connect.url_server_output
                    # create url o read
                    status, ftp = obj_connect.test_connection00(obj_connect)  # Get both status and ftp object
                    if status and ftp:  # Check both status and ftp object
                        _logger.info("Connection successful at CRON!!")
                        try:  # Add try...except block for FTP operations
                            ftp.cwd('/' + str(url_server_output))  # Ensure correct path
                            _logger.info("Ready to write to the server")
                            for attach in files:
                                if not os.path.exists(url_output):
                                    os.makedirs(url_output)
                                if os.path.exists(url_output):
                                    ruta = os.path.join(url_output, attach.name)
                                    with open(ruta, 'wb') as fw_f:
                                        fw_f.write(base64.b64decode(attach.datas))
                                    fw_f.close()
                                    upload_sucessfull = obj_connect.upload(ftp, ruta)
                                    if upload_sucessfull:
                                        _logger.info("Document(s) uploaded to FTP server successfully")
                                        os.remove(ruta)
                                        # remove server
                                        obj_ftp.write({'state': 'send'})
                        except Exception as e:
                            _logger.error(f"FTP Error during upload: {e}")
                            raise UserError(_("FTP error during upload: %s") % e)
                        finally:
                            if ftp:  # Ensure ftp object exists before quitting
                                ftp.quit()
                    else:
                        _logger.warning('FTP connection failed.')
                        raise UserError(_('FTP connection failed.'))
                else:
                    _logger.warning('There is no FTP server configured.')
                    raise UserError(_('There is no FTP server configured.'))
            else:
                _logger.warning('Attachment(s) required.')
                raise UserError(_('Attachment(s) required.'))
            return False
