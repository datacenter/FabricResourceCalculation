from createMo import *

TIME_INTERVAL_CHOICES = ['5 mins', '15 mins', '1 hour', '1 day', '1 week', '1 month', '1 qtr', '1 year']
POL_ENTRY_LIST = ['eqptcapacityPolEntry5min', 'eqptcapacityPolEntry15min', 'eqptcapacityPolEntry1h', 'eqptcapacityPolEntry1d', 'eqptcapacityPolEntry1w', 'eqptcapacityPolEntry1mo', 'eqptcapacityPolEntry1qtr',  'eqptcapacityPolEntry1year']

def input_node_id():
    return input_options('Node ID', '', '', num_accept=True)


def input_time_interval():
    return input_options('Time period', '', TIME_INTERVAL_CHOICES)


def input_optional_args():
    args={'nodes': read_add_mos_args(add_mos('Specify a Node', input_node_id)),
          'time_interval': read_add_mos_args(add_mos('specify a time interval', input_time_interval))}
    return args


class PolicyTcamCalculation(CreateMo):

    def __init__(self):
        self.description = 'Calculate the Policy TCAM resource usage.'
        self.nodes = {}
        self.pol_entry_list = POL_ENTRY_LIST
        self.pol_entry = []
        super(PolicyTcamCalculation, self).__init__()

    def set_cli_mode(self):
        super(PolicyTcamCalculation, self).set_cli_mode()
        self.parser_cli.add_argument('-n', '--nodes', nargs='+', help='List resource of The Nodes. If not specify, all nodes would be shown.')
        self.parser_cli.add_argument('-t', '--time_interval', nargs='+', choices=TIME_INTERVAL_CHOICES, help='The time interval. If no specify, all the time interval will be shown')

    def wizard_mode_input_args(self):
        self.args['optional_args'] = input_optional_args()
    
    def get_fabric_nodes(self):
        nodes = self.look_up_class('fabricNode')
        nodes = [node for node in nodes if str(node.role) != 'controller']
        for n in nodes:
            self.nodes['node-'+str(n.id)] = {}
            self.nodes['node-'+str(n.id)]['role'] = str(n.role)
            for plo_entry in self.pol_entry_list:
                self.nodes['node-'+str(n.id)][plo_entry] = 0

    def count_by_pol_entry(self, pol_entry_class_name):
        pol_entry_mos = self.look_up_class(pol_entry_class_name, set_mo=False)
        for pol_entry_mo in pol_entry_mos:
            node_id = str(pol_entry_mo.dn).split('/')[2]
            value = int(pol_entry_mo.normalizedLast)
            self.counting_percentage(node_id, pol_entry_class_name, value)

    def counting_percentage(self, node_id, pol_entry_class_name, value):
        self.nodes[node_id][pol_entry_class_name] = value

    def read_opt_args(self):
        super(PolicyTcamCalculation, self).read_opt_args()
        if not is_valid_key(self.optional_args, 'time_interval', ban=[[]]):
            self.optional_args['time_interval'] = TIME_INTERVAL_CHOICES
        for time in self.optional_args['time_interval']:
            idx = TIME_INTERVAL_CHOICES.index(time)
            self.pol_entry.append(self.pol_entry_list[idx])
        if not is_valid_key(self.optional_args, 'nodes'):
            self.optional_args['nodes'] = self.nodes

    def print_result2(self):
        for node in self.nodes:
            print '\nFor', node, 'the most current statistics for policy entry: '
            idx = 0
            for time in self.nodes[node]:
                print 'in', self.optional_args['time_interval'][idx], 'interval is', str(self.nodes[node][time]) + '%.'
                idx += 1

    def print_result(self):
        parameters = ['node']
        for t in TIME_INTERVAL_CHOICES:
            if t in (self.optional_args['time_interval']):
                parameters.append(t)
        parameters=tuple(parameters)
        print ("%14s"*len(parameters)% parameters)
        print ("    ----------"*len(parameters))
        for node in sorted(self.nodes, key=self.nodes.get):
            value = [node]
            for time in POL_ENTRY_LIST:
                if is_valid_key(self.nodes[node], time):
                    value.append(str(self.nodes[node][time])+'% ('+str(int(4096*(1-0.01*self.nodes[node][time])))+')')
            value = tuple(value)
            print ("%14s"*len(parameters)% value)

    def main_function(self):
        self.get_fabric_nodes()
        for pol_entry in self.pol_entry_list:
            self.count_by_pol_entry(pol_entry)
        if self.optional_args['nodes'] and type(self.optional_args['nodes']) == list:
            self.optional_args['nodes'] = ['node-' + str(id) for id in self.optional_args['nodes']]
            self.nodes = {k:v for (k,v) in self.nodes.items() if k in self.optional_args['nodes']}
        if len(self.pol_entry) >= 1:
            for i in self.nodes:
                self.nodes[i] = {k:v for (k,v) in self.nodes[i].items() if k in self.pol_entry}
        self.print_result()


if __name__ == '__main__':
    mo = PolicyTcamCalculation()
