'''Dummy example that exports some utility functions to be used by otehr examples.
'''


def pause():
    '''Pause the program execution and wait for the user to press a key to continue.
    '''
    _ = input("Press the <ENTER> key to continue...")
    print()


def tab(lines: str, striplines: bool = False) -> str:
    '''Return a variant of the input string indented by one level.

    #### Arguments
        lines (str): Lines to be indented.
        striplines (bool): Whether to strip() individual lines before re-joining. Defaults to False.

    #### Return
        str: Indented variant of the provided string.
    '''
    return '\n'.join([
        '    ' + (line.strip() if striplines else line)
        for line in lines.splitlines(False)
    ])


if __name__ == '__main__':
    print('This example does nothing, it just exports some utility functions to be used by other',
          'examples.')
