import os
import requests
from shutil import copyfile, chown
from subprocess import Popen
from time import time, sleep
from gelo.configuration import InvalidConfigurationError, is_int
from gelo.architecture import IMediator, IMarkerSource, MarkerType

ICECAST_CONFIG = """<icecast>
    <location>Earth</location>
    <admin>icemaster@localhost</admin>
    <limits>
        <clients>{num_clients}</clients>
        <sources>1</sources>
        <queue-size>524288</queue-size>
        <client-timeout>30</client-timeout>
        <header-timeout>15</header-timeout>
        <source-timeout>10</source-timeout>
    </limits>
    <authentication>
        <source-password>{source_password}</source-password>
        <relay-password>D98Wn2K86948HuXENnZbDAX9CxeGWj3W</relay-password>
        <admin-user>admin</admin-user>
        <admin-password>D98Wn2K86948HuXENnZbDAX9CxeGWj3W</admin-password>
    </authentication>
    <hostname>localhost</hostname>
    <listen-socket>
        <port>{port}</port>
        <bind-address>{bind_address}</bind-address>
    </listen-socket>
    <mount type="normal">
        <mount-name>/traktor.ogg</mount-name>
        <max-listeners>0</max-listeners>
    </mount>
    <fileserve>1</fileserve>
    <paths>
        <!-- basedir is only used if chroot is enabled -->
        <basedir>{basedir}</basedir>
        <logdir>/log/icecast</logdir>
        <webroot>/web</webroot>
        <adminroot>/admin</adminroot>
        <pidfile>/icecast.pid</pidfile>
        <alias source="/" destination="/status.xsl"/>
    </paths>
    <security>
        <chroot>1</chroot>
        <changeowner>
            <user>{unprivileged_user}</user>
            <group>{unprivileged_group}</group>
        </changeowner>
    </security>
</icecast>"""
NOWPLAYING_XSL = """
<xsl:stylesheet xmlns:xsl = "http://www.w3.org/1999/XSL/Transform" version = "1.0">
<xsl:output method="text" encoding="UTF-8" indent="yes" />
<xsl:template match = "/icestats" >
<xsl:for-each select="source">
<xsl:if test="artist"><xsl:value-of select="artist" /> — </xsl:if><xsl:value-of select="title" />
<!-- This next line is required to put a newline after the track name -->
<xsl:text>&#xa;</xsl:text>
</xsl:for-each>
</xsl:template>
</xsl:stylesheet>"""


class Icecast(IMarkerSource):
    """Fork an Icecast server in order to capture chapter marks"""

    def __init__(self, config, mediator: IMediator):
        """Create a new instance of Icecast (the plugin)."""
        super().__init__(config, mediator)
        self.should_terminate = False
        self.last_marker = ''
        self.config_test()
        self.setup_environment()

    def run(self):
        """Run the code that creates markers from Icecast.
        This should be run as a thread."""
        # Fork Icecast
        Popen(['icecast', '-c', self.config['config_file']])
        starttime = time()
        while not self.should_terminate:
            track = self.poll_icecast()
            if track != self.last_marker:
                self.mediator.notify(MarkerType.TRACK, track)
                self.last_marker = track
            sleep(0.25 - ((time() - starttime) % 0.25))

    def poll_icecast(self) -> str:
        """Connect to the Icecast server via HTTP and request the current track.
        :return: The current track, in the format {artist} (em dash) {title}
        """
        return requests.get(
            'http://127.0.0.1:{port}/nowplaying.xsl'.format_map(self.config)
        ).text

    def setup_environment(self):
        """Set up the environment for Icecast, if it isn't already."""
        basedir = self.config['basedir']
        user = self.config['unprivileged_user']
        group = self.config['unprivileged_group']
        # Make sure the Icecast chroot directory exists
        if not (
                os.path.exists(basedir) and
                os.path.isdir(basedir)
        ):
            os.makedirs(basedir, exist_ok=True)
        chown(basedir, user=user, group=group)
        # Make sure the web files directory exists
        web_path = os.path.join(basedir, 'web')
        if not (
                os.path.exists(web_path) and
                os.path.isdir(web_path)
        ):
            os.mkdir(web_path)
        chown(web_path, user=user, group=group)
        # Make sure the admin pages directory exists
        admin_path = os.path.join(basedir, 'admin')
        if not (
                os.path.exists(admin_path) and
                os.path.isdir(admin_path)
        ):
            os.mkdir(admin_path)
        chown(admin_path, user=user, group=group)
        # Make sure the etc directory exists
        etc_path = os.path.join(basedir, 'etc')
        if not (
                os.path.exists(etc_path) and
                os.path.isdir(etc_path)
        ):
            os.mkdir(etc_path)
        chown(basedir, user=user, group=group)
        # Copy /etc/mime.types to {basedir}/etc/mime.types
        # copyfile('/etc/mime.types', os.path.join(etc_path, 'mime.types'))
        # Make sure log directory exists
        log_path = os.path.join(self.config['basedir'], 'log', 'icecast')
        if not (
                os.path.exists(log_path) and
                os.path.isdir(log_path)
        ):
            os.makedirs(log_path)
        chown(log_path, user=user, group=group)
        # Make sure the now playing file exists and has the right contents
        np_file = os.path.join(web_path, "nowplaying.xsl")
        with open(np_file, 'w') as f:
            f.write(NOWPLAYING_XSL)
        # Make sure the Icecast config file exists and has the right contents
        icecast_cfg_file = self.config['config_file']
        with open(icecast_cfg_file, 'w') as f:
            f.write(ICECAST_CONFIG.format_map(self.config))

    def config_test(self):
        """Test the configuration to ensure that it contains the required items.
        Also, convert any configuration items to the right formats, and perform
        variable expansions.
        """
        errors = []
        # Port
        if not 'port' in self.config:
            errors.append('[plugin:icecast] does not have the required key'
                          ' "port"')
        else:
            if not is_int(self.config['port']):
                errors.append('[plugin:icecast] has a non-numeric value for the'
                              'key "port"')
            else:
                if int(self.config['port']) >= 65536:
                    errors.append('[plugin:icecast] has a value greater than'
                                  ' 65535 for the key "port", which is not'
                                  ' supported by TCP')
        # Bind Address
        if not 'bind_address' in self.config:
            errors.append('[plugin:icecast] does not have the required key'
                          ' "bind_address"')
        else:
            if len(self.config['bind_address'].split('.')) != 4:
                errors.append('[plugin:icecast] has a value that does not look'
                              ' like an IP address for the key "bind_address"')
        # Source password
        if not 'source_password' in self.config:
            errors.append('[plugin:icecast] does not have the required key'
                          ' "source_password"')
        # Number of Clients
        if not 'num_clients' in self.config:
            errors.append('[plugin:icecast] does not have the required key'
                          ' "num_clients"')
        # Base directory
        if not 'basedir' in self.config:
            errors.append('[plugin:icecast] does not have the required key'
                          ' "basedir"')
        else:
            self.config['basedir'] = os.path.expandvars(self.config['basedir'])
        # Config file
        if not 'config_file' in self.config:
            errors.append('[plugin:icecast] does not have the required key'
                          ' "config_file"')
        else:
            self.config['config_file'] = \
                os.path.expandvars(self.config['config_file'])
        # Unpriviliged User
        if not 'unprivileged_user' in self.config:
            errors.append('[plugin:icecast] does not have the required key'
                          ' "unprivileged_user"')
        # Unpriviliged Group
        if not 'unprivileged_group' in self.config:
            errors.append('[plugin:icecast] does not have the required key'
                          ' "unprivileged_group"')
        # Throw exception if necessary.
        if len(errors) > 0:
            raise InvalidConfigurationError(errors)
