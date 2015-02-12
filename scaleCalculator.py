# coding=utf-8
"""
“scaleCalculator.py” is scalable. At this moment, “scaleCalculator.py” takes
tenants, stretched tenants, tenant span, tenant constraint, EPG / Tenant,
EPG Span and EPG constraints as key parameters. But you could always add
any other parameters as optional parameters of the script. When you do that,
you need to give it three values: parameter/Tenant, parameter span and
parameter constraints.

The script support three ways of input methods:

1. In yaml mode, you may add any parameter under “parameters”. You may take
 a look at how I put “ep” in they “scaleCalculator.yaml” as a sample.


2. In wizard mode, just follow the instruction.


3. In cli mode, if you only take tenants and EPG into account, please do:

python scaleCalculator.py cli -t 100 0 20 1000 -e 35 20 3500

(the numbers after -t flag are: number of tenant, number of stretched tenant,
tenant span and tenant constraint; the numbers after -e flag are: number of
EPG, EPG span and EPG constraint)
If you want to add one more parameter, you can add a -p flag followed by
3 numbers. e.g.:

python scaleCalculator.py cli -t 100 0 20 1000 -e 35 20 3500 -p 640 2 6000

(here is an example of adding “Ep” into account, which Ep/Tenant =640,
EpSpan=2, EpConstraint=6000)
You may use as many as -p flags as you want.


Of course, yaml mode is always the cleanest way.

-------------------------------------------------------------------------------

Input parameters:
* for tenant:
number, the number of tenants
stretched, the number of stretched tenants
span, the size of a tenant spans
constraint: the upper limit of tenant size that a Tor can contain.
* for epg:
number, the number of epgs
span, the size of a epg spans
constraint: the upper limit of epg size that a Tor can contain.
* other parameters:
number, the number of the parameter
span, the size of a parameter spans
constraint: the upper limit of parameter size that a Tor can contain.
"""


from createMo import *
import math

DEFAULT_CONSTRAINT_PER_TOR = {'tenant': 1000,
                              'epg': 3500,
                              'ep': 6000}


def add_a_parameter():
    key = input_raw_input('Name of the parameter', required=True)
    if key in DEFAULT_CONSTRAINT_PER_TOR.keys():
        default_constraint=DEFAULT_CONSTRAINT_PER_TOR[key]
    else:
        default_constraint=float('inf')
    return input_other_parameter(key, default_constraint)


def input_other_parameter(key, default_constraint=float('inf')):
    para = {'number': input_options('Number of '+key+' per Tenant', 0, [], num_accept=True, required=True),
            'span': input_options('Amount of span per '+key, 0, [], num_accept=True, required=True),
            'constraint': input_options('Constraint of '+key+' per ToR', str(default_constraint), [], num_accept=True)}
    return para


def input_key_parameters():
    tenant = {'number': input_options('Number of Tenants', 0, [], num_accept=True, required=True),
              'stretched': input_options('Number of Stretched Tenants', 0, [], num_accept=True),
              'span': input_options('Amount of span per Tenant', 0, [], num_accept=True, required=True),
              'constraint': input_options('Constraint of Tenant per ToR', str(DEFAULT_CONSTRAINT_PER_TOR['tenant']), [], num_accept=True)}
    epg = input_other_parameter('EPG', default_constraint=DEFAULT_CONSTRAINT_PER_TOR['epg'])

    return tenant, epg


def input_other_parameters():
    para = read_add_mos_args(add_mos("Add a parameter", add_a_parameter))
    return para


def scale_calculator(tenant, epg, other_parameters):

    def get_n_of_tors(para):
        return math.ceil(para['number']*(tenant['number']+tenant['stretched'])*para['span']/float(para['constraint']))

    epp_per_fabric = epg['span']*20

    num_of_tor = max(math.ceil((tenant['number']+tenant['stretched'])*tenant['span']/float(tenant['constraint'])),
                     get_n_of_tors(epg))

    for item in other_parameters:
        num_of_tor = max(num_of_tor, get_n_of_tors(item))
        print num_of_tor

    num_of_epp = (tenant['number'] + tenant['stretched']) * epg['number'] * epg['span']

    return num_of_tor, num_of_epp


class ScaleCalculator(CreateMo):

    def __init__(self):
        self.description = 'Calculate the Number of Switch needed.'
        self.tenant = {}
        self.epg = {}
        self.parameters = []
        super(ScaleCalculator, self).__init__()

    def set_host_user_password(self):
        """No need to login to APIC"""
        pass

    def apic_login(self):
        """No need to login to APIC"""
        pass

    def set_cli_mode(self):
        self.parser_cli.add_argument('-t', '--tenant', nargs=4, help='Number of Tenants, number of stretched tenant, tenant span, maximum tenant per ToR', required=True)
        self.parser_cli.add_argument('-e', '--epg', nargs=3, help='Number of EPG per Tenant, EPG span, maximum EPG per ToR', required=True)
        self.parser_cli.add_argument('-p', '--parameters', nargs=3, action='append', help='Number of parameter per Tenant, parameter span, maximum parameter per ToR', required=True)

    def run_wizard_mode(self):
        self.wizard_mode_input_args()
        self.read_key_args()
        self.read_opt_args()

    def wizard_mode_input_args(self):
        self.args['tenant'], self.args['epg'] = input_key_parameters()
        self.args['parameters'] = input_other_parameters()

    def read_key_args(self):
        if self.config_mode == 'cli':
            self.args['tenant'] = {'number': float(self.args['tenant'][0]),
                                   'stretched': float(self.args['tenant'][1]),
                                   'span': float(self.args['tenant'][2]),
                                   'constraint': float(self.args['tenant'][3])}
            self.args['epg'] = {'number': float(self.args['epg'][0]),
                                'span': float(self.args['epg'][1]),
                                'constraint': float(self.args['epg'][2])
                                }
            parameters = []
            for item in self.args['parameters']:
                parameters.append({'number': float(item[0]),
                                   'span': float(item[1]),
                                   'constraint': float(item[2])})
            self.args['parameters'] = parameters
        self.tenant = self.args.pop('tenant')
        self.epg = self.args.pop('epg')
        self.parameters = self.args.pop('parameters')

    def main_function(self):
        num_of_tor, num_of_epp_in_fabric = scale_calculator(self.tenant, self.epg, self.parameters)
        print 'Number of TORs is: ', num_of_tor
        print 'Number of EpP in Fabric is: ', num_of_epp_in_fabric

if __name__ == '__main__':
    mo = ScaleCalculator()
