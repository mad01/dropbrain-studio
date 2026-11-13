---
title: "python click bash zsh auto complete same files"
date: 2016-04-24
slug: python-click-auto-complete-bash-zsh
description: "Sharing the same auto completion for zsh and bash. In zsh there is somthing called bashcompinit that can be used to share the same completion for bash and zsh. here is a small…"
tags: python, bash, zsh
---
Sharing the same auto completion for zsh and bash. In zsh there is somthing called `bashcompinit` that can be used to share the same completion for bash and zsh. here is a small example project that will fix completion for you when you are not using a nested command structure. see next post about nested completion for bash/zsh

project structur
```bash
├── MANIFEST.in
├── Makefile
├── auto_compleate_install.sh
├── ecli
├── ecli_lib
│   ├── __init__.py
│   └── main.py
├── requirements.txt
└── setup.py
```

click example cli command
```python
#!/usr/bin/env python2
import click

@click.group(help='')
def ecli():
    pass

@click.command('thing')
@click.option('-t', '--thing', help='', required=True)
def bar(thing):
    click.echo(thing)

@click.command('stuff')
@click.option('-s', '--stuff', help='', required=True)
def foo(stuff):
    click.echo(stuff)

ecli.add_command(foo)
ecli.add_command(bar)
```

install script that is run post install
```bash
#!/usr/bin/env bash
if [[ $(basename $SHELL) = 'bash' ]];
then
    if [ -f ~/.bashrc ];
    then
        echo "Installing bash autocompletion..."
        grep -q 'ecli-autocompletion' ~/.bashrc
        if [[ $? -ne 0 ]]; then
            echo "" >> ~/.bashrc
            echo 'eval "$(_ECLI_COMPLETE=source ecli)"' >> ~/.ecli-autocompletion.sh
            echo "source ~/.ecli-autocompletion.sh" >> ~/.bashrc
            echo "source ~/.ecli-complete.sh" >> ~/.bashrc
        fi
    fi
elif [[ $(basename $SHELL) = 'zsh' ]];
then
    if [ -f ~/.zshrc ];
    then
        echo "Installing zsh autocompletion..."
        grep -q 'ecli-autocompletion' ~/.zshrc
        if [[ $? -ne 0 ]]; then
            echo "" >> ~/.zshrc
            echo "autoload bashcompinit" >> ~/.zshrc
            echo "bashcompinit" >> ~/.zshrc
            echo 'eval "$(_ECLI_COMPLETE=source ecli)"' >> ~/.ecli-autocompletion.sh
            echo "source ~/.ecli-autocompletion.sh" >> ~/.zshrc
        fi
    fi
fi
```


setup.py file that runs the post install with auto complete in zsh and bash
```python
from pip.req import parse_requirements
from setuptools import find_packages
from setuptools import setup
from subprocess import call
from setuptools.command.install import install as _install

install_requirements = parse_requirements('requirements.txt', session=False)
requirements = [str(ir.req) for ir in install_requirements]

class install(_install):

    def __post_install(self, dir):
        call(['./auto_compleate_install.sh'])

    def run(self):
        _install.run(self)
        self.execute(
            self.__post_install,
            (self.install_lib,),
            msg="installing auto completion"
            )

setup(
    name='ecli',
    version='0.1a2',
    author=u'example',
    author_email='foo@example.com',
    description='Some description',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'ecli=ecli_lib.main:ecli',
        ]},
    cmdclass={'install': install},
    )
```

The example can be found here. [Source](https://github.com/mad01/examples/tree/master/cli)
