import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-connector-interfaces",
    description="Meta package for oca-connector-interfaces Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-connector_importer>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
