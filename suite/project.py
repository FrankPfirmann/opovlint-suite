
import os
import subprocess
import multiprocessing
import shlex

def setup_openfoam(version):
    subprocess.call(["git", "clone", "https://github.com/OpenFOAM/OpenFOAM-" + str(version) + ".git"])
    subprocess.call(["git", "clone", "https://github.com/OpenFOAM/ThirdParty-" + str(version) + ".git"])


def environ_openfoam(name):
    command = shlex.split("env -i bash -c 'source " + name + "/etc/bashrc && env'")
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    for line in proc.stdout:
        (key, _, value) = line.rstrip().decode("utf-8").partition("=")
        os.environ[key] = value
    proc.communicate()


def preconfigure_openfoam(version):
    os.chdir("ThirdParty-" + version)
    subprocess.call(["./Allwmake"])
    subprocess.call(["./makeParaView"])
    #wmRefresh()
    os.chdir("../../..")


def comgen_openfoam(name):
    os.chdir(name)
    subprocess.call("wmake/wcleanPlatform")
    os.chdir("")
    f = open('Allwmake', "r").readlines()
    for i in range(0, len(f)):
        if "wmake $targetType OpenFOAM" in f[i]:
            f[i] = "bear wmake $targetType OpenFOAM\n"
            f[i+1] = "exit 1\n"
    with open('Allwmake', "w") as file:
        file.writelines(f)
    subprocess.call(["./Allwmake", "-j" + str(multiprocessing.cpu_count())])
    os.chdir("../../..")
    os.rename(os.getcwd() + '/src/compile_commands.json', os.getcwd() + '/compile_commands.json')
    os.chdir("../../..")


def setup_su2(version):
    subprocess.call(["git", "clone", "https://github.com/su2code/SU2.git"])


def environ_su2(name):
    os.environ["SU2_HOME"] = os.getcwd() + "/SU2"
    #os.environ["PATH"] += os.pathsep + os.environ["SU2_RUN"]
    #sys.path.append(os.environ["SU2_RUN"])


def preconfigure_su2(version):
    os.chdir("../../SU2")
    subprocess.call("./bootstrap")
    subprocess.call("./configure")
    os.chdir("../../..")


def comgen_su2(name):
    os.chdir(name)
    subprocess.call(["bear make"], shell=True)
    os.chdir("../../..")


def idle():
    pass


# Setup of a project split into four different phases
# 1. Downloading Source Code (Parameter = version of project)
# 2. Setting up the enviroment (Parameter = full name of project and its directory)
# 3. Preconfigure the project for compiling e.g. building dependent tools(Parameter = version of project)
# 4. Generate the compile commands by adding bear to the wmake command (Parameter = full name of project)
class Project:
    def __init__(self, setup=idle, environ=idle, preconfigure=idle, comgen=idle):
        self.setup = setup
        self.environ = environ
        self.preconfigure = preconfigure
        self.comgen = comgen


openFOAM = Project(setup_openfoam, environ_openfoam, preconfigure_openfoam, comgen_openfoam)
su2 = Project(setup_su2, environ_su2, preconfigure_su2, comgen_su2)
