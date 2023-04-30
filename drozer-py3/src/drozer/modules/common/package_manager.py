import json
from typing import Set, Optional

from pydiesel.reflection import ReflectionException

from . import ClassLoader


class PackageManager(ClassLoader):
    """
    Utility methods for interacting with the Android Package Manager.
    """

    GET_ACTIVITIES = 0x00000001
    GET_CONFIGURATIONS = 0x00004000
    GET_DISABLED_COMPONENTS = 0x00000200
    GET_GIDS = 0x00000100
    GET_INSTRUMENTATION = 0x00000010
    GET_INTENT_FILTERS = 0x00000020
    GET_META_DATA = 0x00000080
    MATCH_DEFAULT_ONLY = 0x00010000
    GET_PERMISSIONS = 0x00001000
    GET_PROVIDERS = 0x00000008
    GET_RECEIVERS = 0x00000002
    GET_RESOLVED_FILTER = 0x00000040
    GET_SERVICES = 0x00000004
    GET_SHARED_LIBRARY_FILES = 0x00000400
    GET_SIGNATURES = 0x00000040
    GET_URI_PERMISSION_PATTERNS = 0x00000800

    PROTECTION_NORMAL = 0
    PROTECTION_DANGEROUS = 1
    PROTECTION_SIGNATURE = 2
    PROTECTION_SIGNATURE_OR_SYSTEM = 3
    PROTECTION_FLAG_SYSTEM = 0x10
    PROTECTION_FLAG_DEVELOPMENT = 0x20
    PROTECTION_FLAG_APPOP = 0x40
    PROTECTION_FLAG_PRE23 = 0x80
    PROTECTION_FLAG_INSTALLER = 0x100
    PROTECTION_FLAG_VERIFIER = 0x200
    PROTECTION_FLAG_PREINSTALLED = 0x400
    PROTECTION_FLAG_SETUP = 0x800
    PROTECTION_FLAG_INSTANT = 0x1000
    PROTECTION_FLAG_RUNTIME_ONLY = 0x2000
    PROTECTION_FLAG_OEM = 0x4000
    PROTECTION_FLAG_VENDOR_PRIVILEGED = 0x8000
    PROTECTION_FLAG_SYSTEM_TEXT_CLASSIFIER = 0x10000
    PROTECTION_FLAG_WELLBEING = 0x20000
    PROTECTION_FLAG_DOCUMENTER = 0x40000
    PROTECTION_FLAG_CONFIGURATOR = 0x80000
    PROTECTION_FLAG_INCIDENT_REPORT_APPROVER = 0x100000
    PROTECTION_FLAG_APP_PREDICTOR = 0x200000

    __package_manager_proxy = None
    perm_cache: Set['PermissionInfo'] = set()

    class NoSuchPackageException(ReflectionException):
        
        def __str__(self):
            return "could not find the package: %s" % self.args

    class PackageManagerProxy(object):
        """
        Wrapper for the native Java PackageManager object, which provides convenience
        methods for handling some of the return types.
        """

        def __init__(self, module):
            self.__module = module
            self.__package_manager = module.getContext().getPackageManager()

        def getLaunchIntentForPackage(self, package):
            """
            Gets the Launch Intent for the specified package.
            """

            return self.__package_manager.getLaunchIntentForPackage(package)

        def getNameForUid(self, uid):
            """
            Gets the name associated with the specified UID.
            """

            return self.__package_manager.getNameForUid(uid)

        def getPackageInfo(self, package, flags=0):
            """
            Get a package's PackageInfo object, optionally passing flags.
            """
            
            try:
                return self.__package_manager.getPackageInfo(package, flags)
            except ReflectionException as e:
                if str(e) == package:
                    raise PackageManager.NoSuchPackageException(package)
                else:
                    raise

        def getPackages(self, flags=0):
            """
            Iterate through all installed packages.
            """

            packages = self.installedPackages(flags)

            for i in range(packages.size()):
                yield packages.get(i)

        def getApplicationLabel(self, package, flags=0):
            """
            Get the 'app_name' string for a package.
            """
            try:
                pkg = self.__package_manager.getApplicationInfo(package, flags)
                return self.__package_manager.getApplicationLabel(pkg)
            except ReflectionException as e:
                if str(e) == package:
                    raise PackageManager.NoSuchPackageException(package)
                else:
                    raise

        def getPackagesForUid(self, uid):
            """
            Get all packages with a specified UID.
            """

            return self.__package_manager.getPackagesForUid(uid)

        def getSourcePaths(self, package):
            """
            Get all source directories associated with a package.
            """

            return self.getPackageInfo(package).applicationInfo.publicSourceDir.split()

        def installedPackages(self, flags=0):
            """
            Get all installed packages, as a Java List<>.
            """

            return self.__package_manager.getInstalledPackages(flags)

        def packageManager(self):
            """
            Get the internal reference to the PackageManager.
            """

            return self.__package_manager

        def queryContentProviders(self, process_name, uid, flags):
            """
            Get Content Provider information.
            """

            providers = self.__package_manager.queryContentProviders(process_name, uid, flags)

            for i in range(providers.size()):
                yield providers.get(i)

        def queryIntentActivities(self, intent, flags):
            """
            Get all Activities that can be launched with a specified Intent.
            """

            activities = self.__package_manager.queryIntentActivities(intent.buildIn(self.__module), flags)

            for i in range(activities.size()):
                yield activities.get(i)


    def packageManager(self):
        """
        Get the Android PackageManager.
        """

        if self.__package_manager_proxy is None:
            self.__package_manager_proxy = PackageManager.PackageManagerProxy(self)

        return self.__package_manager_proxy

    def getAllPermissions(self) -> Set['PermissionInfo']:
        if len(self.perm_cache) == 0:
            permissionHelper = self.loadClass("common/PermissionHelper.apk", "PermissionHelper")
            j_permissions = json.loads(str(permissionHelper.all(self.getContext().getPackageManager())))
            for j_permission in j_permissions:
                self.perm_cache.add(
                    PermissionInfo(protectionLevel=j_permission['protectionLevel'],
                                   name=j_permission['name'],
                                   packageName=j_permission['packageName'], ))
        return self.perm_cache

    def singlePermissionInfo(self, permission: str) -> Optional['PermissionInfo']:
        ret = list(filter(lambda x: x.name == permission, self.getAllPermissions()))
        if len(ret) == 0:
            # If one permission is declared in custom-group, and the custom-group is not declared.
            # 1. That permission is not in `null` group.
            # 2. And custom-group cannot be accessed by PackageManager.getAllPermissionGroups.
            # So, that permission is not in `self.perm_cache`.
            # But we can use PackageManager.getPermissionInfo instead.
            permissionHelper = self.loadClass("common/PermissionHelper.apk", "PermissionHelper")
            str_ret = str(permissionHelper.single(self.getContext().getPackageManager(), permission))
            if str_ret == "":
                return None
            json_ret = json.loads(str_ret)
            _pi = PermissionInfo(protectionLevel=json_ret['protectionLevel'],
                                 name=json_ret['name'],
                                 packageName=json_ret['packageName'], )
            self.perm_cache.add(_pi)
            return _pi
        else:
            return ret[0]


class PackageItemInfo(object):
    def __init__(self, name: str, packageName: str):
        self.name: str = name
        self.packageName: str = packageName

    def __repr__(self):
        return "<PackageItemInfo name=%s,packageName=%s>" % (self.name, self.packageName)

    def __eq__(self, other):
        if not isinstance(other, PackageItemInfo):
            return False
        return self.name == other.name and self.packageName == other.packageName


class PermissionInfo(PackageItemInfo):
    def __init__(self, *, protectionLevel: int, name: str, packageName: str):
        super().__init__(name, packageName)
        self.protectionLevel: int = protectionLevel

    def __repr__(self):
        return "<PermissionInfo protectionLevel=%d,name=%s,packageName=%s>" % (self.protectionLevel, self.name, self.packageName)

    def __hash__(self) -> int:
        return self.packageName.__hash__()
