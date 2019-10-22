opovlint-suite

==============

General

-------

Automatic test suite for static code analysis with the .. _opovlint: https://github.com/ahueck/opovlint/tree/clang6.0 project
Currently supported Projects:

1) .. _OpenFOAM: https://github.com/OpenFOAM/OpenFOAM-6 
2) .. _SU2: https://github.com/su2code/SU2

To add a different project setup, implement the four different phases of setup described in project.py if necessary and create a Project object. Execution of opovlint is also possible for non-supported projects, which requires the compile_commands.json file in the root folder of the analyzed project. The result of the analysis is written into a csv file. For more information about options use "suite.py -h"

Prerequisites

-------------

- C++ Compiler with C++11 support (GCC version >= 4.8)
- Cmake (version >= 2.8)
- Clang/LLVM 6.0
- The executable created by opovlint should be in the path
- All other prerequisites of possible analyzed projects (e.g. zlib for OpenFOAM-6)

