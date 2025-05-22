# -*- coding: utf-8 -*-
##############################################################################
#
#    This module allows to know the geolocation of the employees as well as
#    the electronic devices used once they make the attendance control.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'FTP Transfer File',
    'version': '0.1',
    'summary': 'FTP Transfer File',
    'description': """Transfer File via FTP to a server from odoo""",
    'license': 'AGPL-3',
    'author': "Computs SDN BHD",
    'category': 'Extra Tools',
    'website': "https://www.computs.com.mt",
    'contributors': [
        "Equipo Dev <devtodoo@gmail.com>",
        "Edgar Naranjo <edgarnaranjof@gmail.com>",
        "Shahrul Izlan <msi@computs.com.my>"
    ],
    'support': '',
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/ftp_setting_views.xml',
        'data/ftp_data.xml'
    ],
    'images': [
       'static/description/screenshot_ftp.png'
    ],
    # 'live_test_url': 'https://youtu.be/HNGusvLC6ag',
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 19.99,
    'currency': 'EUR',
}
