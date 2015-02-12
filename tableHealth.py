import paramiko
from createMo import *


def input_leaf_id():
    return str(input_options('Leaf ID', '', '', num_accept=True))


def input_optional_args():
    args={'leaves': read_add_mos_args(add_mos('Specify a Leaf', input_leaf_id))}
    return args


class TableHealth(CreateMo):

    def __init__(self):
        self.description = 'Calculate resource usage.'
        self.tcam = {}
        self.leaf_ids = []
        self.ssh = None
        super(TableHealth, self).__init__()

    def set_cli_mode(self):
        super(TableHealth, self).set_cli_mode()
        self.parser_cli.add_argument('-l', '--leaves', nargs='+', help='List resource of The Leaves. If not specify, all leaves would be shown.')

    def wizard_mode_input_args(self):
        self.args['optional_args'] = input_optional_args()

    def get_leaves(self):
        fvns_ucast_addr_blk = self.look_up_class('fvnsUcastAddrBlk')
        self.get_leaf_ids()
        leaves=[]
        for blk in fvns_ucast_addr_blk:
            curr_switch = {'id': self.get_switch_id(str(blk.dn)),
                           'ip': self.get_switch_ip(blk)}
            if self.is_leaf(curr_switch['id']):
                leaves.append(curr_switch)
        return leaves

    def get_leaf_ids(self):
        listing = []
        if is_valid_key(self.optional_args, 'leaves') and type(self.optional_args['leaves']) == list:
            listing = self.optional_args['leaves']
        for node in self.look_up_class('fabricNode'):
            if node.role == 'leaf':
                if listing != [] and node.id not in listing:
                    continue
                self.leaf_ids.append(str(node.id))

    def is_leaf(self, id):
        return id in self.leaf_ids

    def get_switch_id(self, dn):
        dn = dn.split('/')[2]
        return dn.lstrip('addrinst-oobAddrInst')

    def get_switch_ip(self, blk):
        return str(blk.to)

    def login_switch(self, ip):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(ip, username=self.user, password=self.password)

    def logout_switch(self):
        self.ssh.close()

    def get_sec(self, stdout):
        for line in stdout:
            line = line.split()
            if 'SEC' in line and 'GRP' in line:
                return {'usage': str(line[line.index('usage:')+1]),
                        'size': str(line[line.index('size:')+1])}

    def exec_show_platform_command(self):
        stdin, stdout, stderr = self.ssh.exec_command('vsh_lc -c "show platform internal ns table-health"')
        return self.get_sec(stdout)

    def print_result(self):
        parameters = ['Switch', 'Usage', 'Size', 'Percentage']
        parameters = tuple(parameters)
        print ("%6s %7s %6s %12s "% parameters)
        print ("------   -----   ----   ----------")
        for switch in sorted(self.tcam, key=self.tcam.get):
            switch = self.tcam[switch]
            value = [switch['id'], switch['usage'], switch['size'], switch['percentage']]
            print ("%6s %7s %6s %12s "% tuple(value))

    def main_function(self):
        leaves = self.get_leaves()
        for leaf in leaves:
            self.login_switch(leaf['ip'])
            leaf = dict(list(leaf.items()) + list(self.exec_show_platform_command().items()))
            leaf['percentage'] = str(round(float(leaf['usage'])/float(leaf['size'])*100, 2)) + '%'
            self.tcam[leaf['id']] = leaf
            self.logout_switch()
        self.print_result()


if __name__ == '__main__':

    mo = TableHealth()



