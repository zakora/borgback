from setuptools import find_packages, setup

setup(
    name='borgback',
    version='0.2',
    description='Scheduled backups using Borg',
    author='zakora',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: System :: Archiving :: Backup',
    ],
    packages=['borgback'],
    python_requires='~=3.5',
    entry_points={
        'console_scripts': ['borgback=borgback.backup:main']
    },
    install_requires=[
        'python-dateutil~=2.7',
        'toml~=0.9',
        'xdg~=3.0',
    ],
)
