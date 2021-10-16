import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo8-addons-oca-connector-interfaces",
    description="Meta package for oca-connector-interfaces Odoo addons",
    version=version,
    install_requires=[
        'odoo8-addon-base_import_async',
        'odoo8-addon-test_base_import_async',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 8.0',
    ]
)
