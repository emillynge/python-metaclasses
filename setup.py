from distutils.core import setup
import sys
if sys.version_info < (3, 4):
    print("The use of metaclasses in this package is not supported below 3.4\nPlease upgrade")
    sys.exit(1)

setup(
    name='elymetaclasses',
    version='1.4',
    packages=['elymetaclasses'],
    url='https://github.com/emillynge/python-metaclasses',
    license='GPL v2',
    author='Emil Sauer Lynge',
    author_email='',
    description='a collection of metaclasses',
    classifiers=[
                    # How mature is this project? Common values are
                    #   3 - Alpha
                    #   4 - Beta
                    #   5 - Production/Stable
                    'Development Status :: 3 - Alpha',

                    # Indicate who your project is intended for
                    'Intended Audience :: Developers',

                    # Pick your license as you wish (should match "license" above)
                    'License :: OSI Approved :: GPL v2',

                    # Specify the Python versions you support here. In particular, ensure
                    # that you indicate whether you support Python 2, Python 3 or both.
                    'Programming Language :: Python :: 3.4',
                    'Programming Language :: Python :: 3.5',
                ],
)
