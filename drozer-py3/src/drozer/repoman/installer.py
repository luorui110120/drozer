import io
import os
import re
import zipfile

from xml.etree import ElementTree as xml

from mwr.common import fs

from .remotes import Remote, NetworkException

class ModuleInfo(object):
    """
    ModuleInfo encapsulates the name and human-readable description of a module
    that has been discovered on a remote.
    """
    
    def __init__(self, remote, name, description=None):
        self.name = name
        self.description = description
        self.__remote = remote
    
    def matches(self, pattern):
        """
        True, if the given regex pattern matches the module name.
        """
        
        return re.match(pattern, self.name)
    
    def __eq__(self, other):
        return other is not None and str(self) == str(other)
    
    def __hash__(self):
        return hash(self.name)
    
    def __ne__(self, other):
        return other is None or str(self) != str(other)
    
    def __str__(self):
        return self.name
    
        
class ModuleInstaller(object):
    """
    ModuleInstaller encapsulates methods for installing new modules from the local
    filesystem, or a remote module repository.
    """
    
    def __init__(self, repository):
        self.repository = repository
    
    def install(self, modules, force=False):
        """
        Installs a list of modules, either as local or remote specs, and returns
        a dictionary of status information.
        """

        if force:
            print("Forcing installation of modules from repositories")
        
        status = { 'success': [], 'existing': [], 'fail': {} }

        for pattern in modules:
            if pattern.find("/") >= 0 or pattern.find("\\") >= 0:
                fetch = self.__read_local_module
                _modules = [pattern]
            else:
                try:
                    fetch = self.__read_remote_module
                    _modules = self.search_index(pattern)
                except NetworkException as e:
                    status['fail'][pattern] = str(e)
                    _modules = []
            
            for module in _modules:
                print("Processing %s..." % module, end=' ')
                
                try:
                    self.__install_module(fetch, module, force)
                    print("Done.")
                    
                    status['success'].append(module)
                except AlreadyInstalledError as e:
                    print("Already Installed.")

                    status['existing'].append(module)
                except InstallError as e:
                    print("Failed.")
                    
                    status['fail'][module] = str(e) 
        
        return status
    
    def search_index(self, module):
        """
        Search the combined index view from all remotes based on a search pattern
        with optional wildcards.
        """
        
        index = self.__get_combined_index()

        return sorted([m for m in index if m.matches(".*" + module.replace("*", ".*") + ".*") is not None], key=lambda m: m.name)
    
    def __create_package(self, package):
        """
        Create a Python package within the repository.
        """
        
        if not os.path.exists(package):
            os.makedirs(package)
            # we must make sure that there is an __init__.py is every directory
            # that we have just created, otherwise Python will complain about
            # missing modules
            self.__ensure_packages(package)
        
        return package
    
    def __emit(self, path):
        """
        Write a blank file to a specified path.
        """
        
        fs.touch(path)
    
    def __ensure_packages(self, package):
        """
        Ensure that every directory between the repository root and a specified
        package contains an __init__.py file.
        """
        
        directories = package[len(self.repository):].split(os.path.sep)
        
        for i in range(len(directories)):
            self.__emit(os.path.join(self.repository, *directories[0:i+1] + ["__init__.py"]))
    
    def __get_combined_index(self):
        """
        Fetches INDEX files from all known remotes, and builds a combined INDEX
        listing of all available modules.
        """
        
        index = set([])
        
        for url in Remote.all():
            source = Remote.get(url).download("INDEX.xml")
            
            if source is not None:
                modules = xml.fromstring(source)
                
                index = index.union([ModuleInfo(url, m.attrib['name'], m.find("./description").text) for m in modules.findall("./module")])
        
        return [m for m in index if m is not None and m != ""]

    def __install_module(self, fetch, module, force):
        """
        Install a module into a repository.
        """

        source = fetch(module)
        
        # check that we successfully read source for the module, otherwise there
        # isn't much more we can do here
        if source is None:
            raise InstallError("Failed to get module for '%s'." % module)
        
        return self.__unpack_module(os.path.basename(str(module)), source, force)

    def __read_local_module(self, module):
        """
        Read a module file from the local filesystem, and return the source.
        """
        
        return fs.read(module)
    
    def __read_remote_module(self, module):
        """
        Read a module file from a remote, and return the source.
        """
        
        for url in Remote.all():
            source = Remote.get(url).download(module)
            
            # if we found the source, we return straight away - this allows us to
            # install the module from the first source that we come across
            if source is not None:
                return source
        
        return None
    
    def __unpack_module(self, module, source, force):
        """
        Unpack some module source and install it into the repository. We may have:
        
          - raw python source; or
          - a zip file, containing several sources.
        
        We use the inferred path from the module name to create a package structure
        and either write Python source into the last segment, as a module, or
        unzip a zip file into that folder.
        """
        
        # we test for the presence of a zip header in the source, which we *should*
        # never see in a raw Python file:
        #
        #   0000000 4b50 0403 0014 0000 0000 4122 4192 d6b7
        #   0000010 8e47 117c 0000 117c 0000 000c 0000 7865
        #
        # Because the bytes are in little-endian order, we actually must look for
        # the bytes 50 4b 03 04.
        if source[0:4] == b"\x50\x4b\x03\x04":
            return self.__unpack_module_zip(module, source, force)
        else:
            return self.__unpack_module_raw(module, source, force)
        
        return True
    
    def __unpack_module_raw(self, module, source, force=False):
        """
        Handles unpacking a module and installing it, if the source is a Python
        module.
        """
        
        path = module.split(".")
        
        # create a Python package to write the module into
        package = self.__create_package(os.path.join(self.repository, *path[0:-1]))
        
        # calculate the path where we will write the module
        path = os.path.join(package, path[-1] + ".py")
        # ensure that we are not about to overwrite an existing module
        if os.path.exists(path) and not force:
            raise AlreadyInstalledError("The target (%s) already exists in the repository." % module)
        # write the module file into the package
        if fs.write(path, source) is not None:
            return True
        else:
            raise InstallError("Failed to write module to repository.")
        
    def __unpack_module_zip(self, module, source, force=False):
        """
        Handles unpacking a module and installing it, if the source is a zipped
        archive.
        """
        
        path = module.split(".")[0:-1]
        # when extracting the path, we drop the last segment, because it'll be '.zip'
        
        # create a Python package to write the module into
        package = self.__create_package(os.path.join(self.repository, *path))
        
        # get a list of files within the archives
        archive = zipfile.ZipFile(io.BytesIO(source))
        files = archive.infolist()
        # if force is set, we dont care if it overwrites an existing file
        # ensure we are not about to overwrite any existing files
        if True in [f.filename != "__init__.py" and f.filename != ".drozer_package" and os.path.exists(os.path.join(package, f.filename)) for f in files] and not force:
            raise AlreadyInstalledError("Installing this module would overwrite one-or-more files in your repository.")
        # extract each file, in turn
        try:
            for f in files:
                archive.extract(f, package)
        except IOError:
            raise InstallError("Fatal error whilst unpacking the zip archive.")
        
        return True
            
class InstallError(Exception):
    """
    Raised if there was a problem installing a module.
    """
    
    pass

class AlreadyInstalledError(InstallError):
    """
    Raised if a requested module is already installed.
    """
    
    pass
