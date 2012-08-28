import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages
setup(
    name = "django-sorting",
    version = "0.2",
    packages = ["sorting"],
    py_modules = ['setup', 'ez_setup'],
    author = "Thiago Carvalho",
    author_email ="thiagocavila@gmail.com", 
    description = "Sort arbitrary querysets in templates.",
    url = "http://github.com/staticdev/django-sorting",
    include_package_data = True
)
