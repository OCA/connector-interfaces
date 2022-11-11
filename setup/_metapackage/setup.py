import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-connector-interfaces",
    description="Meta package for oca-connector-interfaces Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-connector_importer>=15.0dev,<15.1dev',
        'odoo-addon-connector_importer_source_sftp>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
