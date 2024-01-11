# QASP solver

<!-- TODO -->

## Build instructions

### Python virtual environment

I strongly recommend using a [Python virtual environment](https://docs.python.org/3/library/venv.html) to install all the required dependencies, in order to avoid (possibly) messing with other Python projects you may be working with.

A new `venv` can be created by running the following command:

```sh
python -m venv ./.py-venv --prompt qasp-solver
```

To enter (and then quit) the environment, the following commands can be used from the directory where the `venv` folder was created:

```sh
source ./.py-venv/bin/activate # Enter the venv
deactivate # Quit the venv
```

The rest of this section assumes that you run all the provided commands while inside the virtual environment.

### Dependencies

First of all, install the Python dependencies specified in the `requirements.txt` file:

```sh
pip install -r ./requirements.txt
```

At the time of writing, the version of the [`tweedledum` library](https://pypi.org/project/tweedledum/) packaged by [PyPI](https://pypi.org/) is broken, thus it cannot be installed with `pip`. Instead, use the following commands to download, build, and install it from the publicly available sources:

```sh
# Install build dependencies (Ubuntu)
sudo apt install -y wget gcc g++ cmake ninja-build

# Setup build folder
WORKDIR=`pwd`
mkdir build && cd ./build
mkdir lib-tweedledum && cd ./lib-tweedledum

# Download and unpack sources
wget https://files.pythonhosted.org/packages/source/t/tweedledum/tweedledum-1.1.1.tar.gz \
    https://github.com/boschmitt/tweedledum/pull/170.patch \
    https://github.com/pybind/pybind11/archive/refs/tags/v2.10.4.tar.gz
tar xvf tweedledum-1.1.1.tar.gz && tar xvf v2.10.4.tar.gz
cd ./tweedledum-1.1.1

# Patch sources
patch --forward --strip=1 --input="../170.patch"
cd ./external
rm -r pybind11 && mv ../../pybind11-2.10.4 pybind11
cd ../include/tweedledum/IR
sed -i '6s/.*/#include <cstdint>/' ./Cbit.h
cd ../../..
sed -i 's/project/option/' ./pyproject.toml

# Install library
python ./setup.py build
pip install .

# Cleanup
cd ${WORKDIR} && unset WORKDIR
```

Optionally, you can check that the installation was successful by listing the installed libraries:

```sh
pip list | grep 'tweedledum'
```
