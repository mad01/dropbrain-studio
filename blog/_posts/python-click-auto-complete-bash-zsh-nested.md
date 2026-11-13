---
title: "python click bash zsh auto complete same files nested command groups"
date: 2016-04-24
slug: python-click-auto-complete-bash-zsh-nested
description: "Sharing the same auto completion for zsh and bash. In zsh there is somthing called bashcompinit that can be used to share the same completion for bash and zsh. here is a small…"
tags: python, bash, zsh, nested
---
Sharing the same auto completion for zsh and bash. In zsh there is somthing called `bashcompinit` that can be used to share the same completion for bash and zsh. here is a small example project that will fix completion with command groups and nested commands.

project structur
```bash
├── MANIFEST.in
├── Makefile
├── auto_compleate_install.sh
├── ecli-complete-nested.sh
├── ecli-nested
├── ecli_nested_lib
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

@ecli.group(help='')
def cmd1():
    pass

@ecli.group(help='')
def cmd2():
    pass

@cmd1.group(help='')
def foo():
    pass

@cmd2.group(help='')
def bar():
    pass

ecli.add_command(cmd1)
ecli.add_command(cmd2)

cmd1.add_command(foo)
cmd2.add_command(bar)

@foo.command('do_thing')
@click.option('-t', '--thing', help='', required=True)
def foo_do_thing(thing):
    click.echo(thing)

@bar.command('do_stuff')
@click.option('-s', '--stuff', help='', required=True)
def bar_do_stuff(stuff):
    click.echo(stuff)
```

install script that is run post install
```bash
#!/usr/bin/env bash
if [[ $(basename $SHELL) = 'bash' ]];
then
    if [ -f ~/.bashrc ];
    then
        echo "Installing bash autocompletion"
        cp ecli-complete-nested.sh ~/.ecli-complete-nested.sh
        grep -q 'ecli-complete-nested' ~/.bashrc
        if [[ $? -ne 0 ]]; then
            echo "" >> ~/.bashrc
            echo "source ~/.ecli-complete-nested.sh" >> ~/.bashrc
        fi
    fi
elif [[ $(basename $SHELL) = 'zsh' ]];
then
    if [ -f ~/.zshrc ];
    then
        echo "Installing zsh autocompletion"
        cp ecli-complete-nested.sh ~/.ecli-complete-nested.sh
        grep -q 'ecli-complete-nested' ~/.zshrc
        if [[ $? -ne 0 ]]; then
            echo "" >> ~/.zshrc
            echo "autoload bashcompinit" >> ~/.zshrc
            echo "bashcompinit" >> ~/.zshrc
            echo "source ~/.ecli-complete-nested.sh" >> ~/.zshrc
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
    name='ecli_nested',
    version='0.1a1',
    author=u'example',
    author_email='foo@example.com',
    description='Some description',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'ecli-nested=ecli_nested_lib.main:ecli',
        ]},
    cmdclass={'install': install},
    )
```

completion file for bash that can be used with zsh
```bash
_ecli()
{
    local cur prev

    cur=${COMP_WORDS[COMP_CWORD]}
    prev=${COMP_WORDS[COMP_CWORD-1]}

    case ${COMP_CWORD} in
        1)
            COMPREPLY=($(compgen -W "cmd1 cmd2" ${cur}))
            ;;
        2)
            case ${prev} in
                cmd1)
                    COMPREPLY=($(compgen -W "foo" ${cur}))
                    ;;
                cmd2)
                    COMPREPLY=($(compgen -W "bar" ${cur}))
                    ;;
            esac
            ;;
        3)
            case ${prev} in
                foo)
                    COMPREPLY=($(compgen -W "do_thing" ${cur}))
                    ;;
                bar)
                    COMPREPLY=($(compgen -W "do_stuff" ${cur}))
                    ;;
            esac
            ;;
        *)
            COMPREPLY=()
            ;;
    esac
}

complete -F _ecli ecli\-nested
```


The example can be found here. [Source](https://github.com/mad01/examples/tree/master/cli_nested)
