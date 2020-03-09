import setuptools

with open('README.md') as fp:
    long_description = fp.read()

setuptools.setup(
    name='del2rpp',
    version='0.1.0',
    description='Tool for converting Synthstrom Audible Deluge songs to REAPER projects',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Dillon Cower',
    license='MIT',
    url='https://github.com/dcower/del2rpp',
    packages=setuptools.find_packages(),
    install_requires=[
        'attrs',
        'pydel',
        'rpp',
    ],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Multimedia :: Sound/Audio :: Conversion',
        'Topic :: Utilities',
    ])