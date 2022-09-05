from setuptools import find_packages, setup
setup(
    name='hydro_visualiser',
    packages=find_packages(include=['hydro_visualiser']),
    version='0.1.0',
    description='First Hydro-visualiser library',
    author='Me',
    license='AGH',
    install_requires=[],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests',
)