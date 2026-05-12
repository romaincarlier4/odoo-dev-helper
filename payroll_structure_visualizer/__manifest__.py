{
    'name': 'Payroll Structure Visualizer',
    'version': '1.0',
    'author': 'romc',
    'category': 'Human Resources/Payroll',
    'summary': 'Visualize salary structures and shared salary rules in a hierarchy view',
    'depends': ['hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'views/payroll_structure_visualizer_views.xml',
        'views/payroll_structure_visualizer_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'payroll_structure_visualizer/static/src/css/visualizer.css',
            'payroll_structure_visualizer/static/src/css/rule_graph.css',
            'payroll_structure_visualizer/static/src/js/payroll_structure_visualizer.js',
            'payroll_structure_visualizer/static/src/js/payroll_rule_graph.js',
            'payroll_structure_visualizer/static/src/xml/payroll_structure_visualizer.xml',
            'payroll_structure_visualizer/static/src/xml/payroll_rule_graph.xml',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': ['hr_payroll'],
}
