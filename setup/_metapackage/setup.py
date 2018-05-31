import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-oca-connector-interfaces",
    description="Meta package for oca-connector-interfaces Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-base_import_async',
        'odoo10-addon-test_base_import_async',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
