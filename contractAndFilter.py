from createMo import *
from moStore import *

import os

try:
    import external_c_functions
except ImportError:
    print 'External c functions has not been installed into your system.'
    print 'Installing external c functions...'
    os.system('sudo python setup.py install')
    import external_c_functions


DONNER = 'N9K-M6PQ'
MILLER = 'N9K-M12PQ'


def input_leaf_id():
    return str(input_options('Leaf ID', '', '', num_accept=True))


def input_optional_args():
    args={'leaves': read_add_mos_args(add_mos('Specify a Leaf', input_leaf_id))}
    return args


class ContractAndFilterResourceCalculation(CreateMo):

    def __init__(self):
        self.description = 'Calculate the Contract and Filters resource usage.'
        self.node_tcam = {'999': {'policy_tcam': 0, 'app_tcam': 0}}  # number of TCAM entries
        self.numTCAMEntries = 16  # average size?
        self.contracts_list = {} # a list that record all the registered contracts (have both providers and consumers)
        super(ContractAndFilterResourceCalculation, self).__init__()

    def set_cli_mode(self):
        super(ContractAndFilterResourceCalculation, self).set_cli_mode()
        self.parser_cli.add_argument('-l', '--leaves', nargs='+', help='List resource of The Leaves. If not specify, all leaves would be shown.')

    def wizard_mode_input_args(self):
        self.args['optional_args'] = input_optional_args()

    def set_up_fabric_node(self):
        nodes = self.look_up_class('eqptLC')
        for node in nodes:
            node_id = self.get_key_value(str(node.dn), 'node')
            node_model = node.model
            self.node_tcam[node_id] = {'policy_tcam': 0, 'app_tcam': 0}
            if node_model == DONNER:
                self.node_tcam[node_id]['policy_tcam_limit'] = 65536
                self.node_tcam[node_id]['app_tcam_limit'] = 2048
            elif node_model == MILLER:
                self.node_tcam[node_id]['policy_tcam_limit'] = 4096
                self.node_tcam[node_id]['app_tcam_limit'] = 512
            else:
                self.node_tcam[node_id]['policy_tcam_limit'] = 0
                self.node_tcam[node_id]['app_tcam_limit'] = 0

    def two_are_same_mo(self, short_string, long_string):
        """
        :return: True if two string match
        """
        return short_string == long_string[:len(short_string)]

    def get_rsprov_scope(self, rsprov):
        """
        :param rsprov: provided contract
        :return: the scope of the contract
        """
        # for contract in self.modir.lookupByClass('vzBrCP', parentDn=rsprov):
        #     if str(contract.dn) == str(rsprov.tDn):
        contract = self.modir.lookupByDn(str(rsprov.tDn))
        return str(contract.scope)

    def get_provider(self, rsprov):
        """
        :param rsprov: provided contract
        :return: the provider epg
        """
        for epg in self.mos.gbl_fvAEPg:
            if self.two_are_same_mo(str(epg.dn), str(rsprov.dn)):
                return epg

    def get_rscons(self, rsprov):
        """
        :param rsprov: provided contract
        :return: the corresponding consumed contracts.
        """
        rscons = []
        for fvrscons in self.mos.gbl_fvRsCons:
            if str(rsprov.tDn) == str(fvrscons.tDn):
                rscons.append(fvrscons)
        return rscons

    def get_consumers(self, rscons):
        """
        :param rscons: consumed contract
        :return: consumer epg
        """
        for epg in self.mos.gbl_fvAEPg:
            if self.two_are_same_mo(str(epg.dn), str(rscons.dn)):
                return epg

    def get_key_value(self, args, prefix):
        """
        :param args:  dn or tDn
        :param prefix: any prefix within the input dn or tDn
        :return: the string after the prefix
        """
        if type(args) == str:
            args = args.split('/')
        if not prefix.endswith('-'):
            prefix += '-'
        arg = [i for i in args if str.startswith(i, prefix)]
        if len(arg) == 1:
            return arg[0][len(prefix):]
        else:
            return None

    def get_epg_info(self, args):
        """
        :param args: dn
        :return: tenant and application of the epg.
        """
        return {'tenant': self.get_key_value(args, 'tn'),
                'application': self.get_key_value(args, 'ap'),
                'epg': self.get_key_value(args, 'epg')}

    def is_same_key_value(self, epg1, epg2, key):
        """
        :param epg1: EPG, could be provider or consumer
        :param epg2: EPG, could be provider or consumer
        :param key:  key value
        :return:   True if two epgs have the same value.
        """
        epg1 = self.get_epg_info(str(epg1.dn))
        epg2 = self.get_epg_info(str(epg2.dn))
        if epg1[key] == epg2[key]:
            return True
        else:
            return False

    def look_up_epg_context(self, epg):
        """
        :param epg:  EPG, could be provider or consumer
        :return: the context (private network) of the input EPG
        """
        rsbd = self.look_up_epg_rsbd(epg)
        rsCtx = self.look_up_rsCtx_from_rsbd(rsbd)
        return rsCtx.tnFvCtxName

    def look_up_epg_rsbd(self, epg):
        """
        :param epg: EPG
        :return: the bridge-donmain of the EPG
        """
        for rsbd in self.mos.gbl_fvRsBd:
            if self.two_are_same_mo(str(epg.dn), str(rsbd.dn)):
                return rsbd

    def look_up_rsCtx_from_rsbd(self, rsbd):
        """
        :param rsbd: bridge domain of EPG
        :return: the context where the BD locates.
        """
        for rsCtx in self.mos.gbl_fvRsCtx:
            if self.two_are_same_mo(str(rsbd.tDn), str(rsCtx.dn)):
                return rsCtx

    def get_contract_subjects(self, contract):
        """
        :param contract: a contract
        :return: all the subjects under the contract
        """
        subjects = []
        for vzSubj in self.mos.gbl_vzSubj:
            if self.two_are_same_mo(str(contract.tDn), str(vzSubj.dn)):
                subjects.append(vzSubj)
        return subjects

    def get_rsfilters(self, subject):
        """
        :param subject: contract subject
        :return: all the filters that are included in the subject.
        """
        rsfilters = []
        for filter in self.mos.gbl_vzRsSubjFiltAtt:
            if self.two_are_same_mo(str(subject.dn), str(filter.dn)):
                rsfilters.append(filter)
        return rsfilters

    def get_filter_entries(self, filter_object):
        """
        :param filter: filter
        :return: filter_entries
        """
        return self.look_up_class('vzEntry', set_mo=False, parentDn=str(filter_object.tDn))

    def get_count_from_port_range(self, from_port, to_port):
        """
        :param from_port: port range from
        :param to_port: port range to
        :return: count value
        """
        from_port = 0 if from_port=='unspecified' else int(from_port)
        to_port = 65535 if to_port=='unspecified' else int(to_port)
        return external_c_functions.expand_port_range(from_port, to_port)

    def get_node_ids(self, epg):
        """
        :param epg: epg
        :return: the Node ID where the epg deployed
        """
        paths = self.look_up_class('fvRsPathAtt', set_mo=False, parentDn=epg.dn)
        deployed_node = []
        for path in paths:
            id = self.get_key_value(str(path.tDn), 'paths')
            if not id or not id != None:
                id = self.get_key_value(str(path.tDn), 'protpaths')
                if id:
                    id = id.split('-')
                else:
                    continue
            deployed_node.append(id)
        return deployed_node if deployed_node != [] else ['999']

    def if_reach_tcam_limit(self, node, tcam):
        """
        :param node: node id
        :param tcam: policy_tcam or app_tcam
        :return: turn if tcam limit is reach
        """
        return self.node_tcam[node][tcam] >= self.node_tcam[node][tcam+'_limit']

    def add_tcam(self, node, s_count, d_count, both_direction=False):
        """
        :param node: node id
        :param s_count: source count from get_count_from_port_range
        :param d_count: destination count from get_count_from_port_range
        :param both_direction: when true this function run twice
        :return: None
        """
        if d_count > 3 and not self.if_reach_tcam_limit(node, 'app_tcam'):
            self.node_tcam[node]['app_tcam'] += 1
            self.node_tcam[node]['policy_tcam'] += s_count

        else:
            self.node_tcam[node]['policy_tcam'] += s_count * d_count

        if both_direction:
            self.add_tcam(node, s_count, d_count)

        # print 'policy_tcam', node, s_count, d_count, both_direction, self.node_tcam[node]['policy_tcam']
        # print 'app_tcam', node, s_count, d_count, both_direction, self.node_tcam[node]['app_tcam']

    def print_result(self):
        """
        :return: print how much resource has been occupied on each Node.
        """

        def get_percentage(value, limit):
            return round(100.*value/limit, 2)
        space = '20'
        template = '{0:' + space + '} {1:' + space + '} {2:' + space + '}'
        print template.format("Fabric Nodes", "Policy Tcam", "App Tcam")
        print template.format("------------", "-----------", "--------")
        for rec in sorted(self.node_tcam):
            if is_valid_key(self.optional_args, 'leaves') and rec not in self.optional_args['leaves']:
                continue
            if rec == '999' or self.node_tcam[rec]['policy_tcam_limit'] == 0:
                print template.format(rec, str(self.node_tcam[rec]['policy_tcam']), str(self.node_tcam[rec]['app_tcam']))
            else:
                policy_tcam_precent = get_percentage(self.node_tcam[rec]['policy_tcam'], self.node_tcam[rec]['policy_tcam_limit'])
                policy_tcam_usage = str(self.node_tcam[rec]['policy_tcam']) + '/' + str(self.node_tcam[rec]['policy_tcam_limit']) + '(' + str(policy_tcam_precent) + '%)'
                app_tcam_precent = get_percentage(self.node_tcam[rec]['app_tcam'], self.node_tcam[rec]['app_tcam_limit'])
                app_tcam_usage = str(self.node_tcam[rec]['app_tcam']) + '/' + str(self.node_tcam[rec]['app_tcam_limit']) + '(' + str(app_tcam_precent) + '%)'
                print template.format(rec, policy_tcam_usage, app_tcam_usage)

    def main_function(self):
        """
        Main procedures of the script.
        """
        self.mos = ctrctMOStore(self.modir) # obtain all the mos listed on moStore.py
        self.set_up_fabric_node()  # check out the fabric structure

        # look for all the rsProv. Each rsProv should have ONE provider.
        # In this case, the un-used contracts will be ignore.
        for rsProv in self.mos.gbl_fvRsProv:
            scope = self.get_rsprov_scope(rsProv)
            provider = self.get_provider(rsProv)
            all_consumers = []

            # find all the consumers regardless the scope.
            if provider:
                rsCons = self.get_rscons(rsProv)
                if rsCons:
                    for rsCon in rsCons:
                        cc = self.get_consumers(rsCon)
                        if cc:
                            all_consumers.append(cc)
            if not all_consumers:
                # TODO: Bon, not sure how to deal with a contract that has not consumers.
                continue

            # Take scope into consideration. Selects consumers which agree with the scope.
            consumers = []

            if scope == 'global':
                consumers = all_consumers
            elif scope == 'tenant':
                for consumer in all_consumers:
                    # check if provider and consumer are under the same tenant.
                    if self.is_same_key_value(provider, consumer, 'tenant'):
                        consumers.append(consumer)
            elif scope == 'application-profile':
                for consumer in all_consumers:
                    # check if provider and consumer are under the same tenant and application.
                    if self.is_same_key_value(provider, consumer, 'tenant') and self.is_same_key_value(provider, consumer, 'application'):
                        consumers.append(consumer)
            elif scope == 'context':
                for consumer in all_consumers:
                    # check if provider and consumer are under the same context.
                    if self.look_up_epg_context(provider) == self.look_up_epg_context(consumer):
                        consumers.append(consumer)
            else:
                print('Invalid contract without scope.')

            if not consumers:
                # TODO: Bon, not sure how to deal with a contract that has not consumers.
                continue

            node_ids = self.get_node_ids(provider) * len(consumers)
            for consumer in consumers:
                node_ids.extend(self.get_node_ids(consumer))

            # get all the subjects of the contract.
            subjects = self.get_contract_subjects(rsProv)
            if not subjects:
                continue

            # get all the filters of each subject, thus all the filters of the contract.
            for subject in subjects:
                both_direction = subject.revFltPorts == 'yes'

                rsfilters = self.get_rsfilters(subject)
                for ft in rsfilters:
                    filter_entries = self.get_filter_entries(ft)
                    for fe in filter_entries:
                        s_count = self.get_count_from_port_range(fe.sFromPort, fe.sToPort)
                        d_count = self.get_count_from_port_range(fe.dFromPort, fe.dToPort)
                        # print '-----', rsProv.dn, str(fe.dn), fe.dFromPort, fe.dToPort, s_count, d_count
                        for node_id in node_ids:
                            self.add_tcam(node_id, s_count, d_count, both_direction=both_direction)

        self.print_result()

if __name__ == '__main__':

    mo = ContractAndFilterResourceCalculation()


"""
        policy / app
Milla M12PQ: 4K/ 512
Donner M6PQ: 64k/ 2k

count = port_range(from, to)

value of from and to could be obtained from filter entry.

Scount = port_range(sfrom, sto)
Dcount = port_range(dfrom, dto)

if Dcount > 3:
policy_tcam += Scount
app_tcam += 1

if Dcount <=3:
policy_tcam += Scount * Dcount

Once app_tcam exceed
policy_tcam += Scount * Dcount


"""