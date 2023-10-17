import os
from setuptools import setup, find_packages

# single source of truth for package version
version_ns = {}
with open(os.path.join('globus_app_flows', 'version.py')) as f:
    exec(f.read(), version_ns)
version = version_ns['__version__']

install_requires = []
with open('requirements.txt') as reqs:
    for line in reqs.readlines():
        req = line.strip()
        if not req or req.startswith('#'):
            continue
        install_requires.append(req)


setup(
    name='django_globus_app_flows',
    description='Django Globus App Flows',
    url='https://github.com/globus-gladier/gladier',
    maintainer='The Gladier Team',
    maintainer_email='',
    version=version,
    packages=find_packages(),
    install_requires=install_requires,
    dependency_links=[],
    license='Apache 2.0',
    classifiers=[]
)
