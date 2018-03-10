from setuptools import setup


setup(name='botium',
	include_package_data=True,
    version='1.0.1',
    description='ChatBot Building Framework for Python',
    classifiers=[
        'Topic :: Scientific/Engineering :: Human Machine Interfaces',
        'Framework :: Robot Framework',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: Apache Software License',
    ],
    url='http://github.com/botium/botium',
    author='Deniss Stepanovs',
    author_email='bellatrics@gmail.com',
    license='Apache 2.0',
    packages=['botium'],
    install_requires=[],

    test_suite='nose.collector',
    tests_require=['nose'],

    zip_safe=False)