from os import path
from setuptools import setup, find_packages
from gitlab_sync import __about__

base = path.dirname(__file__)

with open(path.join(base, 'requirements.txt')) as req:
    requirements = req.read()

with open(path.join(base, 'README.md')) as rm:
    readme = rm.read()

setup(name=__about__.__title__,
    version='0.0.1-dev',
    author='David Schneider',
    author_email='david.schneider@bivab.de',
    url='http://tuatara.cs.uni-duesseldorf.de/bivab/gitlab-sync.git',
    description='Utility to synchronize a GitLab group of repositories at once.',
    long_description=readme,
    packages=find_packages(),
    zip_safe=False,
    install_requires=requirements,
    license='MIT',
    include_package_data=False,
    entry_points={
        'console_scripts': [
            'gitlab-sync = gitlab_sync.client:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Version Control',
        'Topic :: System :: Archiving :: Mirroring',
    ],
)

