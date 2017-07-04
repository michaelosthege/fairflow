
from setuptools import setup

__packagename__ = "fairflow"

def get_version():
    import os, re
    VERSIONFILE = os.path.join(__packagename__, '__init__.py')
    initfile_lines = open(VERSIONFILE, 'rt').readlines()
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    for line in initfile_lines:
        mo = re.search(VSRE, line, re.M)
        if mo:
            return mo.group(1)
    raise RuntimeError('Unable to find version string in %s.' % (VERSIONFILE,))

__version__ = get_version()


setup(name = __packagename__,
      packages = [__packagename__], # this must be the same as the name above
      version=__version__,
      description="Functional airflow.",
      url="https://github.com/michaelosthege/fairflow",
      download_url = 'https://github.com/michaelosthege/fairflow/tarball/%s' % __version__,
      author="Michael Osthege",
      author_email="thecakedev@hotmail.com",
      copyright="(c) Copyrights 2017 Zymergen, Inc., Michael Osthege",
      license="MIT",
      classifiers= [
        "Programming Language :: Python",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Intended Audience :: Developers"
      ]
   )

# Installation into the active Python environment
# Local:
#   python setup.py install
# from just outside of the package folder.


# Local, linking to original sources:
#   python setup.py develop
# from just outside of the package folder.

# Uploading to an artifactory index:
#    python setup.py sdist register -r artifactory upload -r artifactory
