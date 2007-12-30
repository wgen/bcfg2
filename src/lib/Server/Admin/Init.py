import os, socket
import Bcfg2.Server.Admin

from Bcfg2.Settings import settings

config = '''
[server]
repository = %s
structures = Bundler,Base
generators = SSHbase,Cfg,Pkgmgr,Rules

[statistics]
sendmailpath = /usr/sbin/sendmail
database_engine = sqlite3
# 'postgresql', 'mysql', 'mysql_old', 'sqlite3' or 'ado_mssql'.
database_name =
# Or path to database file if using sqlite3.
#<repository>/etc/brpt.sqlite is default path if left empty
database_user =
# Not used with sqlite3.
database_password =
# Not used with sqlite3.
database_host =
# Not used with sqlite3.
database_port =
# Set to empty string for default. Not used with sqlite3.
web_debug = True


[communication]
protocol = xmlrpc/ssl
password = %s
key = %s/bcfg2.key

[components]
bcfg2 = %s
'''

groups = '''
<Groups version='3.0'>
   <Group profile='true' public='false' default='true' name='basic'>
      <Group name='%s'/>
   </Group>
   <Group name='ubuntu'/>
   <Group name='debian'/>
   <Group name='freebsd'/>
   <Group name='gentoo'/>
   <Group name='redhat'/>
   <Group name='suse'/>
   <Group name='mandrake'/>
   <Group name='solaris'/>
</Groups>
'''
clients = '''
<Clients version="3.0">
   <Client profile="basic" pingable="Y" pingtime="0" name="%s"/>
</Clients>
'''

os_list = [('Redhat/Fedora/RHEL/RHAS/Centos', 'redhat'),
           ('SUSE/SLES', 'suse'),
           ('Mandrake', 'mandrake'),
           ('Debian', 'debian'),
           ('Ubuntu', 'ubuntu'),
           ('Gentoo', 'gentoo'),
           ('FreeBSD', 'freebsd')]


class Init(Bcfg2.Server.Admin.Mode):
    __shorthelp__ = 'bcfg2-admin init'
    __longhelp__ = __shorthelp__ + '\n\tCompare two client specifications or directories of specifications'
    def __call__(self, args):
        Bcfg2.Server.Admin.Mode.__call__(self, args)
        repopath = raw_input( "location of bcfg2 repository [/var/lib/bcfg2]: " )
        if repopath == '':
            repopath = '/var/lib/bcfg2'
        password = ''
        while ( password == '' ):
            password = raw_input(
                "Input password used for communication verification: " )
        server = "https://%s:6789" % socket.getfqdn()
        rs = raw_input( "Input the server location [%s]: " % server)
        if rs:
            server = rs
        #create the groups.xml file
        prompt = '''Input base Operating System for clients:\n'''
        for entry in os_list:
            prompt += "%d: \n" % (os_list.index(entry) + 1, entry[0])
        prompt += ': '
        os_sel = os_list[int(raw_input(prompt))-1][1]
        self.initializeRepo(repopath, server, password, os_sel)
        print "Repository created successfuly in %s" % (repopath)

    def initializeRepo(self, repo, server_uri, password, os_selection):
        '''Setup a new repo'''
        keypath = os.path.dirname(os.path.abspath(settings.CONFIG_FILE))
        confdata = config % ( repo, password, keypath, server_uri )
        open(settings.CONFIG_FILE,"w").write(confdata)
        # FIXME automate ssl key generation
        os.popen('openssl req -x509 -nodes -days 1000 -newkey rsa:1024 -out %s/bcfg2.key -keyout %s/bcfg2.key' % (keypath, keypath))
        try:
            os.chmod('%s/bcfg2.key'% keypath,'0600')
        except:
            pass
    
        for subdir in ['SSHbase', 'Cfg', 'Pkgmgr', 'Rules', 'etc', 'Metadata',
                       'Base', 'Bundler']:
            path = "%s/%s" % (repo, subdir)
            newpath = ''
            for subdir in path.split('/'):
                newpath = newpath + subdir + '/'
                try:
                    os.mkdir(newpath)
                except:
                    continue
            
        open("%s/Metadata/groups.xml"%repo, "w").write(groups % os_selection)
        #now the clients file
        open("%s/Metadata/clients.xml"%repo, "w").write(clients % socket.getfqdn())

