# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#
import typing as tp
import argparse


class ControllerGeneratorParser:
    """Parse the controller generator specification from cmdline arguments.

    Used later to create generator classes to make modifications to template
    input files.

    Format for pair is: ``<category>.<controller>``.

    Return:

      Parsed controller specification, the generator is missing from the command
      line altogether; this can occur if the user is only running stage [4,5],
      and is not an error. In that case, None is returned.

    """

    def __call__(self, args: argparse.Namespace) -> tp.Optional[str]:
        if args.controller is None:
            return None

        return args.controller  # type: ignore


__api__ = [
    'ControllerGeneratorParser'
]
