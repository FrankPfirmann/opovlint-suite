===============
opovlint-suite
===============

-------
General
-------

Automatic test suite for static code analysis with the opovlint_ project

Currently supported Projects:

1) OpenFOAM_

2) SU2_

.. _OpenFOAM: https://github.com/OpenFOAM/OpenFOAM-6/
.. _SU2: https://github.com/su2code/SU2
.. _opovlint: https://github.com/ahueck/opovlint/tree/clang6.0

To add a different project setup, implement the four different phases of setup described in project.py if necessary and create a Project object. Execution of opovlint is also possible for non-supported projects, which requires the compile_commands.json file in the root folder of the analyzed project.

Use suite/core.py (as a script or as a imported function) to install projects and do project executions

Use suite/evaldb.py to do comparisons and evaluations of executions in a database

Command line option "-h" for both scripts as

Multiple active types cause matches to not be clearly associatable to a matchtype

-------------
Prerequisites
-------------

- C++ Compiler with C++11 support (GCC version >= 4.8)
- Cmake (version >= 2.8)
- Clang/LLVM 6.0
- Generated find-type executable in a bin folder of an OO-Lint instance
- All other prerequisites of possible analyzed projects (e.g. zlib for OpenFOAM-6)

