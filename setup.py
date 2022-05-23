from setuptools import setup

try:
    import PySide6
    install_requires = ['PySide6']
except ImportError:
    install_requires = ['PySide2']

setup(
    name='QPrimaryFlightDisplay',
    version='1.0.0a1',
    description='T-standard compliant primary flight display widget for showing realtime flight data',
    author='Tolga Demirdal',
    url='https://github.com/shadymeowy/QPrimaryFlightDisplay',
    install_requires=install_requires,
    py_modules=["QPrimaryFlightDisplay",]
)
